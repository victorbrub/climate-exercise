# Prediction Module

Climate and economic data analysis using LLMs and statistical methods.

## Setup

### 1. Install Dependencies

```bash
cd prediction
pip install -r requirements.txt
```

### 2. Configure Credentials

Copy the template and add your API keys:

```bash
cp config/config.yaml.template config/config.yaml
nano config/config.yaml  # Edit with your credentials
```

**config.yaml structure:**
```yaml
api_keys:
  github_token: "ghp_your_token_here"
  anthropic_key: "sk-ant-your_key_here"

models:
  github_default: "gpt-4o-mini"
  anthropic_default: "claude-3-haiku-20240307"

analysis:
  max_records: 10
  temperature: 0.7
  max_tokens: 1024
```

**Alternative:** Use environment variables instead:
```bash
export GITHUB_TOKEN="your_token"
export ANTHROPIC_API_KEY="your_key"
```

### 3. Verify Configuration

```bash
python config/config.py
```

## Usage

### Statistical Analysis (No API needed)

```bash
python data_analyzer.py ../example/files/api_results_SP.POP.TOTL.json
```

### GitHub Models API

```bash
python github_predictor.py ../example/files/api_results_SP.POP.TOTL.json
python github_predictor.py ../example/files/api_results_SP.POP.TOTL.json gpt-4o
```

### Claude API

```bash
python claude_predictor.py ../example/files/api_results_SP.POP.TOTL.json
```

### Analyze Predictions

```bash
# Analyze a single prediction file
python github_analyzer.py prediction_github_api_results_SP.POP.TOTL.txt

# Analyze all predictions in directory
python github_analyzer.py .
```

## Python API

```python
from prediction import GitHubModelsPredictor, ClaudePredictor, analyze_climate_data

# Config is loaded automatically
github_pred = GitHubModelsPredictor()
result = github_pred.predict("../example/files/api_results_SP.POP.TOTL.json")

# Statistical analysis
analysis = analyze_climate_data("../example/files/api_results_SP.POP.TOTL.json")
```

## Files

- `config/config.py` - Configuration manager
- `config/config.yaml.template` - Template for credentials
- `config/config.yaml` - Your credentials (git-ignored)
- `github_predictor.py` - GitHub Models API integration
- `claude_predictor.py` - Anthropic Claude API integration
- `github_analyzer.py` - Analyze prediction outputs
- `data_analyzer.py` - Statistical analysis (no API)
- `output/` - All prediction and analysis outputs

## Getting API Keys

- **GitHub Token**: https://github.com/settings/tokens (free)
- **Anthropic Key**: https://console.anthropic.com/ (paid)
