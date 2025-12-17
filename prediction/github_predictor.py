"""
GitHub Models API integration for climate and economic data predictions.
Uses GitHub's free model marketplace with models like GPT-4o, Claude, Llama, etc.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import requests

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


class GitHubModelsPredictor:
    """
    Wrapper for GitHub Models API to make predictions on climate and economic data.
    GitHub Models provides free access to various AI models including GPT-4o, Claude, and more.
    """
    
    # Available models on GitHub
    MODELS = {
        "gpt-4o": "gpt-4o",
        "gpt-4o-mini": "gpt-4o-mini",
        "claude-3.5-sonnet": "claude-3.5-sonnet",
        "claude-3-5-sonnet": "claude-3.5-sonnet",  # Alternative format
        "meta-llama-3.1-405b": "meta-llama-3.1-405b-instruct",
        "llama-3.1-405b": "meta-llama-3.1-405b-instruct",  # Short name
        "phi-3.5": "phi-3.5-mini-instruct",
        "phi-3.5-mini": "phi-3.5-mini-instruct"  # Alternative format
    }
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize GitHub Models predictor with API key.
        
        Args:
            api_key: GitHub Personal Access Token. If not provided, reads from config.yaml or GITHUB_TOKEN env var.
            model: Model to use. If not provided, reads from config.yaml.
                   Options: gpt-4o, gpt-4o-mini, claude-3.5-sonnet, meta-llama-3.1-405b, phi-3.5
        """
        config = get_config()
        self.api_key = api_key or config.get_github_token()
        if not self.api_key:
            raise ValueError(
                "API key required. Set in config.yaml, GITHUB_TOKEN environment variable, "
                "or pass api_key parameter.\n"
                "Get your token at: https://github.com/settings/tokens"
            )
        
        model_name = model or config.get_github_model()
        self.model = self.MODELS.get(model_name, model_name)
        self.settings = config.get_analysis_settings()
        self.base_url = "https://models.inference.ai.azure.com"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
    
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
        Prepare a concise summary of the data for the model.
        
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
        Make a prediction or analysis using GitHub Models based on the data file.
        
        Args:
            data_filepath: Path to the JSON data file
            question: Specific question to ask. If None, asks for general trend analysis.
            
        Returns:
            Model's response text
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
        
        # Call GitHub Models API
        payload = {
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "model": self.model,
            "temperature": self.settings.get('temperature', 0.7),
            "max_tokens": self.settings.get('max_tokens', 1024)
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=self.headers,
            json=payload,
            timeout=30
        )
        
        # Better error handling
        if response.status_code != 200:
            error_detail = ""
            try:
                error_data = response.json()
                error_detail = f"\nAPI Error: {error_data.get('error', {}).get('message', 'Unknown error')}"
            except:
                error_detail = f"\nResponse: {response.text[:200]}"
            
            raise Exception(
                f"GitHub Models API request failed with status {response.status_code}. "
                f"Check your GITHUB_TOKEN is valid and the model '{self.model}' is available.{error_detail}"
            )
        
        result = response.json()
        
        return result['choices'][0]['message']['content']
    
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
            Model's comparative analysis
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
        
        payload = {
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "model": self.model,
            "temperature": self.settings.get('temperature', 0.7),
            "max_tokens": 1500
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=self.headers,
            json=payload,
            timeout=30
        )
        
        # Better error handling
        if response.status_code != 200:
            error_detail = ""
            try:
                error_data = response.json()
                error_detail = f"\nAPI Error: {error_data.get('error', {}).get('message', 'Unknown error')}"
            except:
                error_detail = f"\nResponse: {response.text[:200]}"
            
            raise Exception(
                f"GitHub Models API request failed with status {response.status_code}. "
                f"Check your GITHUB_TOKEN is valid and the model '{self.model}' is available.{error_detail}"
            )
        
        result = response.json()
        
        return result['choices'][0]['message']['content']
    
    def list_available_models(self) -> None:
        """Print available models."""
        print("Available models:")
        for name, model_id in self.MODELS.items():
            print(f"  - {name}: {model_id}")


def predict_trends_github(data_filepath: str, api_key: Optional[str] = None, model: str = "gpt-4o-mini") -> str:
    """
    Convenience function to quickly get predictions for a data file using GitHub Models.
    
    Args:
        data_filepath: Path to JSON data file
        api_key: Optional GitHub token
        model: Model to use (default: gpt-4o-mini)
        
    Returns:
        Prediction text
    """
    predictor = GitHubModelsPredictor(api_key=api_key, model=model)
    return predictor.predict(data_filepath)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python github_predictor.py <path_to_json_file> [model]")
        print("Example: python github_predictor.py ../example/files/api_results_SP.POP.TOTL.json")
        print("Example: python github_predictor.py ../example/files/api_results_SP.POP.TOTL.json gpt-4o")
        print("\nAvailable models:")
        print("  - gpt-4o-mini (default, fast and free)")
        print("  - gpt-4o (more capable)")
        print("  - claude-3.5-sonnet")
        print("  - meta-llama-3.1-405b")
        print("  - phi-3.5")
        print("\nSet GITHUB_TOKEN environment variable with your GitHub Personal Access Token")
        print("Get token at: https://github.com/settings/tokens")
        sys.exit(1)
    
    data_file = sys.argv[1]
    
    # Check if second argument is a valid model name or another file
    model = None
    if len(sys.argv) > 2:
        arg = sys.argv[2]
        # If it looks like a file path, ignore it (from wildcard expansion)
        if not arg.endswith('.json') and not '/' in arg:
            model = arg
    
    try:
        predictor = GitHubModelsPredictor(model=model)
        print(f"Using model: {predictor.model}")
        print(f"Analyzing {data_file}...\n")
        prediction = predictor.predict(data_file)
        print("=" * 80)
        print("MODEL'S ANALYSIS:")
        print("=" * 80)
        print(prediction)
        
        # Save to file
        output_dir = Path(__file__).parent / "output"
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / f"prediction_github_{Path(data_file).stem}.txt"
        with open(output_file, 'w') as f:
            f.write(f"Model: {predictor.model}\n")
            f.write("=" * 80 + "\n")
            f.write(prediction)
        print(f"\n\nPrediction saved to: {output_file}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
