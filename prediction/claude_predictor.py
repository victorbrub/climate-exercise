"""
Claude API integration for climate and economic data predictions.
Uses Anthropic's Claude Haiku model to analyze trends and make predictions.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import anthropic

# Handle both direct execution and module import
try:
    from .config.config import get_config
except ImportError:
    try:
        from config.config import get_config
    except ImportError:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent / "config"))
        from config import get_config


class ClaudePredictor:
    """
    Wrapper for Claude API to make predictions on climate and economic data.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize Claude predictor with API key.
        
        Args:
            api_key: Anthropic API key. If not provided, reads from config.yaml or ANTHROPIC_API_KEY env var.
            model: Model to use. If not provided, reads from config.yaml.
        """
        config = get_config()
        self.api_key = api_key or config.get_anthropic_key()
        if not self.api_key:
            raise ValueError(
                "API key required. Set in config.yaml, ANTHROPIC_API_KEY environment variable, "
                "or pass api_key parameter."
            )
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = model or config.get_anthropic_model()
        self.settings = config.get_analysis_settings()
    
    def load_data_file(self, filepath: str) -> Dict[str, Any]:
        """
        Load JSON data file.
        
        Args:
            filepath: Path to JSON file
            
        Returns:
            Parsed JSON data
        """
        with open(filepath, 'r') as f:
            return json.load(f)
    
    def prepare_data_summary(self, data: Dict[str, Any], max_records: Optional[int] = None) -> str:
        """
        Prepare a concise summary of the data for Claude.
        
        Args:
            data: Full data dictionary
            max_records: Maximum number of records to include (uses config default if None)
            
        Returns:
            Formatted string summary
        """
        if max_records is None:
            max_records = self.settings.get('max_records', 10)
        
        indicator = data.get('indicator', 'Unknown')
        timestamp = data.get('timestamp', 'Unknown')
        records = data.get('data', {}).get('data', [])[:max_records]
        
        summary = f"Indicator: {indicator}\n"
        summary += f"Timestamp: {timestamp}\n"
        summary += f"Total records: {len(data.get('data', {}).get('data', []))}\n\n"
        summary += "Sample data:\n"
        
        for record in records:
            country = record.get('country', {}).get('value', 'Unknown')
            date = record.get('date', 'Unknown')
            value = record.get('value', 'N/A')
            summary += f"- {country} ({date}): {value}\n"
        
        return summary
    
    def predict(self, data_filepath: str, question: Optional[str] = None) -> str:
        """
        Make a prediction or analysis using Claude based on the data file.
        
        Args:
            data_filepath: Path to the JSON data file
            question: Specific question to ask. If None, asks for general trend analysis.
            
        Returns:
            Claude's response text
        """
        # Load data
        data = self.load_data_file(data_filepath)
        data_summary = self.prepare_data_summary(data)
        
        # Prepare prompt
        if question is None:
            question = "Analyze the trends in this data and provide insights about future predictions."
        
        prompt = f"""You are a data analyst specializing in climate and economic trends. 
        
Here is the data summary:

{data_summary}

Question: {question}

Please provide:
1. Key trends observed in the data
2. Potential predictions for the next 5-10 years
3. Factors that might influence these predictions
4. Any notable patterns or anomalies

Keep your response concise and data-driven."""
        
        # Call Claude API
        message = self.client.messages.create(
            model=self.model,
            max_tokens=self.settings.get('max_tokens', 1024),
            temperature=self.settings.get('temperature', 0.7),
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        return message.content[0].text
    
    def batch_predict(self, data_dir: str, question: Optional[str] = None) -> Dict[str, str]:
        """
        Run predictions on multiple data files in a directory.
        
        Args:
            data_dir: Directory containing JSON data files
            question: Question to ask about each dataset
            
        Returns:
            Dictionary mapping filename to prediction
        """
        data_path = Path(data_dir)
        results = {}
        
        for json_file in data_path.glob("*.json"):
            print(f"Processing {json_file.name}...")
            try:
                prediction = self.predict(str(json_file), question)
                results[json_file.name] = prediction
            except Exception as e:
                results[json_file.name] = f"Error: {str(e)}"
        
        return results
    
    def compare_indicators(self, filepaths: List[str], comparison_question: str) -> str:
        """
        Compare multiple indicators and provide insights.
        
        Args:
            filepaths: List of paths to JSON data files
            comparison_question: Question about the comparison
            
        Returns:
            Claude's comparative analysis
        """
        summaries = []
        for filepath in filepaths:
            data = self.load_data_file(filepath)
            summary = self.prepare_data_summary(data, max_records=5)
            summaries.append(f"File: {Path(filepath).name}\n{summary}\n")
        
        combined_summary = "\n---\n".join(summaries)
        
        prompt = f"""You are analyzing multiple related datasets. Here are the summaries:

{combined_summary}

Question: {comparison_question}

Please provide a comparative analysis focusing on:
1. Relationships between the indicators
2. Correlations or patterns across datasets
3. Insights for policy or decision-making
4. Future outlook considering all indicators together"""
        
        message = self.client.messages.create(
            model=self.model,
            max_tokens=1500,
            temperature=self.settings.get('temperature', 0.7),
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        return message.content[0].text


def predict_trends(data_filepath: str, api_key: Optional[str] = None) -> str:
    """
    Convenience function to quickly get predictions for a data file.
    
    Args:
        data_filepath: Path to JSON data file
        api_key: Optional Anthropic API key
        
    Returns:
        Prediction text
    """
    predictor = ClaudePredictor(api_key=api_key)
    return predictor.predict(data_filepath)


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python claude_predictor.py <path_to_json_file>")
        print("Example: python claude_predictor.py ../example/files/api_results_SP.POP.TOTL.json")
        sys.exit(1)
    
    data_file = sys.argv[1]
    
    try:
        predictor = ClaudePredictor()
        print(f"Analyzing {data_file}...\n")
        prediction = predictor.predict(data_file)
        print("=" * 80)
        print("CLAUDE'S ANALYSIS:")
        print("=" * 80)
        print(prediction)
        
        # Save to file
        output_dir = Path(__file__).parent / "output"
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / f"prediction_{Path(data_file).stem}.txt"
        with open(output_file, 'w') as f:
            f.write(prediction)
        print(f"\n\nPrediction saved to: {output_file}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
