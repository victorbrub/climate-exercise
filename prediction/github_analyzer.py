"""
GitHub Models API - Statistical data analyzer that processes results.
Analyzes prediction outputs from GitHub Models API.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from collections import Counter
import re


class GitHubAnalyzer:
    """
    Analyzer for GitHub Models API predictions and responses.
    """
    
    def __init__(self):
        """Initialize the analyzer."""
        self.analyses = []
    
    def load_prediction(self, filepath: str) -> str:
        """
        Load a prediction text file.
        
        Args:
            filepath: Path to prediction text file
            
        Returns:
            Prediction text content
        """
        with open(filepath, 'r') as f:
            return f.read()
    
    def extract_key_points(self, text: str) -> List[str]:
        """
        Extract key points from prediction text.
        
        Args:
            text: Prediction text
            
        Returns:
            List of key points/sentences
        """
        # Split by common bullet points or numbers
        lines = text.split('\n')
        key_points = []
        
        for line in lines:
            line = line.strip()
            # Check if line starts with bullet point, number, or contains key phrases
            if (line.startswith(('-', '•', '*', '1.', '2.', '3.', '4.', '5.')) or
                any(phrase in line.lower() for phrase in ['key trend', 'prediction', 'factor', 'pattern'])):
                if len(line) > 20:  # Avoid very short lines
                    key_points.append(line)
        
        return key_points
    
    def extract_numerical_predictions(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract numerical predictions and dates from text.
        
        Args:
            text: Prediction text
            
        Returns:
            List of numerical predictions with context
        """
        predictions = []
        
        # Look for patterns like "by 2030", "in 2025", etc.
        year_pattern = r'(?:by|in|until|around)\s+(\d{4})'
        
        # Look for percentages
        percent_pattern = r'(\d+(?:\.\d+)?)\s*%'
        
        # Look for large numbers (millions, billions)
        number_pattern = r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*(million|billion|thousand)'
        
        years = re.findall(year_pattern, text)
        percents = re.findall(percent_pattern, text)
        numbers = re.findall(number_pattern, text)
        
        if years:
            predictions.append({
                'type': 'years_mentioned',
                'values': list(set(years)),
                'count': len(years)
            })
        
        if percents:
            predictions.append({
                'type': 'percentages',
                'values': [float(p) for p in percents],
                'count': len(percents)
            })
        
        if numbers:
            predictions.append({
                'type': 'large_numbers',
                'values': numbers,
                'count': len(numbers)
            })
        
        return predictions
    
    def sentiment_analysis(self, text: str) -> Dict[str, Any]:
        """
        Basic sentiment analysis of prediction text.
        
        Args:
            text: Prediction text
            
        Returns:
            Sentiment indicators
        """
        text_lower = text.lower()
        
        # Positive indicators
        positive_words = ['increase', 'growth', 'rising', 'improvement', 'positive', 
                         'expansion', 'progress', 'upturn', 'gain', 'advance']
        
        # Negative indicators
        negative_words = ['decrease', 'decline', 'falling', 'reduction', 'negative',
                         'contraction', 'deterioration', 'downturn', 'loss', 'drop']
        
        # Uncertainty indicators
        uncertainty_words = ['may', 'might', 'could', 'possible', 'uncertain',
                            'variable', 'depends', 'unclear', 'potential']
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        uncertainty_count = sum(1 for word in uncertainty_words if word in text_lower)
        
        total = positive_count + negative_count + uncertainty_count
        
        return {
            'positive_indicators': positive_count,
            'negative_indicators': negative_count,
            'uncertainty_indicators': uncertainty_count,
            'sentiment_score': (positive_count - negative_count) / max(total, 1),
            'overall_tone': self._determine_tone(positive_count, negative_count, uncertainty_count)
        }
    
    def _determine_tone(self, positive: int, negative: int, uncertainty: int) -> str:
        """Determine overall tone of text."""
        if uncertainty > (positive + negative):
            return "cautious/uncertain"
        elif positive > negative * 1.5:
            return "optimistic"
        elif negative > positive * 1.5:
            return "pessimistic"
        else:
            return "balanced"
    
    def analyze_prediction_file(self, filepath: str) -> Dict[str, Any]:
        """
        Comprehensive analysis of a prediction file.
        
        Args:
            filepath: Path to prediction text file
            
        Returns:
            Analysis results
        """
        text = self.load_prediction(filepath)
        
        # Extract model info if present
        model = "unknown"
        if text.startswith("Model:"):
            model_line = text.split('\n')[0]
            model = model_line.replace("Model:", "").strip()
        
        analysis = {
            'filename': Path(filepath).name,
            'model': model,
            'word_count': len(text.split()),
            'line_count': len(text.split('\n')),
            'key_points': self.extract_key_points(text),
            'numerical_predictions': self.extract_numerical_predictions(text),
            'sentiment': self.sentiment_analysis(text),
        }
        
        self.analyses.append(analysis)
        return analysis
    
    def compare_predictions(self, filepaths: List[str]) -> Dict[str, Any]:
        """
        Compare multiple prediction files.
        
        Args:
            filepaths: List of prediction file paths
            
        Returns:
            Comparative analysis
        """
        analyses = [self.analyze_prediction_file(fp) for fp in filepaths]
        
        return {
            'total_predictions': len(analyses),
            'models_used': list(set(a['model'] for a in analyses)),
            'avg_word_count': sum(a['word_count'] for a in analyses) / len(analyses),
            'sentiment_distribution': {
                a['filename']: a['sentiment']['overall_tone']
                for a in analyses
            },
            'individual_analyses': analyses
        }
    
    def batch_analyze_directory(self, directory: str, pattern: str = "prediction_*.txt") -> Dict[str, Any]:
        """
        Analyze all prediction files in a directory.
        
        Args:
            directory: Directory path
            pattern: File pattern to match
            
        Returns:
            Batch analysis results
        """
        dir_path = Path(directory)
        files = list(dir_path.glob(pattern))
        
        if not files:
            return {'error': f'No files matching {pattern} found in {directory}'}
        
        return self.compare_predictions([str(f) for f in files])
    
    def generate_summary_report(self, analysis: Dict[str, Any]) -> str:
        """
        Generate a human-readable summary report.
        
        Args:
            analysis: Analysis results
            
        Returns:
            Formatted report text
        """
        report = "=" * 80 + "\n"
        report += "GITHUB MODELS PREDICTION ANALYSIS REPORT\n"
        report += "=" * 80 + "\n\n"
        
        if 'error' in analysis:
            return report + f"Error: {analysis['error']}\n"
        
        report += f"Total Predictions Analyzed: {analysis['total_predictions']}\n"
        report += f"Models Used: {', '.join(analysis['models_used'])}\n"
        report += f"Average Word Count: {analysis['avg_word_count']:.0f}\n\n"
        
        report += "Sentiment Distribution:\n"
        for filename, tone in analysis['sentiment_distribution'].items():
            report += f"  - {filename}: {tone}\n"
        
        report += "\n" + "-" * 80 + "\n"
        report += "DETAILED ANALYSES:\n"
        report += "-" * 80 + "\n\n"
        
        for pred in analysis['individual_analyses']:
            report += f"\nFile: {pred['filename']}\n"
            report += f"Model: {pred['model']}\n"
            report += f"Words: {pred['word_count']}, Lines: {pred['line_count']}\n"
            report += f"Sentiment: {pred['sentiment']['overall_tone']} "
            report += f"(score: {pred['sentiment']['sentiment_score']:.2f})\n"
            
            if pred['key_points']:
                report += f"\nKey Points ({len(pred['key_points'])}):\n"
                for i, point in enumerate(pred['key_points'][:5], 1):
                    report += f"  {i}. {point[:100]}...\n"
            
            if pred['numerical_predictions']:
                report += "\nNumerical Predictions:\n"
                for num_pred in pred['numerical_predictions']:
                    report += f"  - {num_pred['type']}: {num_pred['count']} mentions\n"
            
            report += "\n"
        
        return report
    
    def save_analysis(self, analysis: Dict[str, Any], output_file: str) -> None:
        """
        Save analysis results to JSON file.
        
        Args:
            analysis: Analysis results
            output_file: Output file path
        """
        with open(output_file, 'w') as f:
            json.dump(analysis, f, indent=2)
        print(f"Analysis saved to: {output_file}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python github_analyzer.py <prediction_file_or_directory> [more_files...]")
        print("Example: python github_analyzer.py prediction_github_api_results_SP.POP.TOTL.txt")
        print("Example: python github_analyzer.py . (analyze all predictions in current dir)")
        print("Example: python github_analyzer.py file1.txt file2.txt file3.txt")
        print("Example: python github_analyzer.py ../example/files/*.json")
        sys.exit(1)
    
    paths = sys.argv[1:]
    analyzer = GitHubAnalyzer()
    
    try:
        # If single path and it's a directory, analyze directory
        if len(paths) == 1 and Path(paths[0]).is_dir():
            print(f"Analyzing all predictions in directory: {paths[0]}\n")
            analysis = analyzer.batch_analyze_directory(paths[0])
        # If multiple paths or single file, analyze those files
        else:
            # Filter out directories and only keep files
            files = [p for p in paths if Path(p).is_file()]
            
            if not files:
                print("Error: No valid files found")
                sys.exit(1)
            
            if len(files) == 1:
                print(f"Analyzing prediction file: {files[0]}\n")
                analysis = analyzer.analyze_prediction_file(files[0])
                analysis = {'total_predictions': 1, 'models_used': [analysis['model']], 
                           'avg_word_count': analysis['word_count'],
                           'sentiment_distribution': {analysis['filename']: analysis['sentiment']['overall_tone']},
                           'individual_analyses': [analysis]}
            else:
                print(f"Analyzing {len(files)} prediction files...\n")
                analysis = analyzer.compare_predictions(files)
        
        # Generate and print report
        report = analyzer.generate_summary_report(analysis)
        print(report)
        
        # Save JSON analysis
        output_dir = Path(__file__).parent / "output"
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / "github_analysis_results.json"
        analyzer.save_analysis(analysis, str(output_file))
        
        # Save text report
        report_file = output_dir / "github_analysis_report.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        print(f"Report saved to: {report_file}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
