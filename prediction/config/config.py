"""
Configuration manager for prediction module.
Loads credentials and settings from config.yaml file.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


class Config:
    """
    Configuration manager for API keys and model settings.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration from YAML file or environment variables.
        
        Args:
            config_path: Path to config.yaml file. If None, looks in current directory
                        and prediction directory.
        """
        self.config_data = {}
        self.config_path = None
        
        # Try to find and load config file
        if config_path:
            self.config_path = config_path
        else:
            # Try common locations
            possible_paths = [
                "config/config.yaml",
                "prediction/config/config.yaml",
                Path(__file__).parent / "config" / "config.yaml",
                Path(__file__).parent.parent / "config" / "config.yaml"
            ]
            
            for path in possible_paths:
                if Path(path).exists():
                    self.config_path = str(path)
                    break
        
        if self.config_path and Path(self.config_path).exists():
            with open(self.config_path, 'r') as f:
                self.config_data = yaml.safe_load(f) or {}
    
    def get_github_token(self) -> Optional[str]:
        """
        Get GitHub token from config or environment variable.
        
        Returns:
            GitHub token or None
        """
        # Try config file first
        token = self.config_data.get('api_keys', {}).get('github_token')
        if token:
            return token
        
        # Fall back to environment variable
        return os.getenv('GITHUB_TOKEN')
    
    def get_anthropic_key(self) -> Optional[str]:
        """
        Get Anthropic API key from config or environment variable.
        
        Returns:
            Anthropic API key or None
        """
        # Try config file first
        key = self.config_data.get('api_keys', {}).get('anthropic_key')
        if key:
            return key
        
        # Fall back to environment variable
        return os.getenv('ANTHROPIC_API_KEY')
    
    def get_github_model(self) -> str:
        """
        Get default GitHub model from config.
        
        Returns:
            Model name (default: gpt-4o-mini)
        """
        return self.config_data.get('models', {}).get('github_default', 'gpt-4o-mini')
    
    def get_anthropic_model(self) -> str:
        """
        Get default Anthropic model from config.
        
        Returns:
            Model name (default: claude-3-haiku-20240307)
        """
        return self.config_data.get('models', {}).get('anthropic_default', 'claude-3-haiku-20240307')
    
    def get_analysis_settings(self) -> Dict[str, Any]:
        """
        Get analysis settings from config.
        
        Returns:
            Dictionary with max_records, temperature, max_tokens
        """
        defaults = {
            'max_records': 10,
            'temperature': 0.7,
            'max_tokens': 1024
        }
        
        settings = self.config_data.get('analysis', {})
        return {**defaults, **settings}
    
    def validate(self) -> Dict[str, bool]:
        """
        Validate that required credentials are available.
        
        Returns:
            Dictionary showing which credentials are available
        """
        return {
            'github_token': bool(self.get_github_token()),
            'anthropic_key': bool(self.get_anthropic_key()),
            'config_file_loaded': bool(self.config_path)
        }
    
    def print_status(self) -> None:
        """Print configuration status."""
        validation = self.validate()
        
        print("Configuration Status:")
        print(f"  Config file loaded: {validation['config_file_loaded']}")
        if self.config_path:
            print(f"  Config path: {self.config_path}")
        print(f"  GitHub token available: {validation['github_token']}")
        print(f"  Anthropic key available: {validation['anthropic_key']}")
        print(f"  Default GitHub model: {self.get_github_model()}")
        print(f"  Default Anthropic model: {self.get_anthropic_model()}")


# Global config instance
_config = None


def get_config(config_path: Optional[str] = None) -> Config:
    """
    Get or create global config instance.
    
    Args:
        config_path: Optional path to config file
        
    Returns:
        Config instance
    """
    global _config
    if _config is None or config_path:
        _config = Config(config_path)
    return _config


if __name__ == "__main__":
    # Test configuration
    config = get_config()
    config.print_status()
    
    print("\nAnalysis settings:")
    settings = config.get_analysis_settings()
    for key, value in settings.items():
        print(f"  {key}: {value}")
