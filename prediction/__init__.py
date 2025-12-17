"""
Prediction module for climate and economic data analysis using LLMs.
"""

from .claude_predictor import ClaudePredictor, predict_trends
from .github_predictor import GitHubModelsPredictor, predict_trends_github
from .github_analyzer import GitHubAnalyzer
from .data_analyzer import analyze_climate_data, load_indicator_data
from .config.config import Config, get_config

__all__ = [
    'ClaudePredictor',
    'predict_trends',
    'GitHubModelsPredictor',
    'predict_trends_github',
    'GitHubAnalyzer',
    'analyze_climate_data',
    'load_indicator_data',
    'Config',
    'get_config'
]
