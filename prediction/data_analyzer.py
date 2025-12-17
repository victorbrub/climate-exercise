"""
Statistical and analytical functions for climate and economic data.
Provides data analysis without using LLMs.
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from collections import defaultdict
import statistics


def load_indicator_data(filepath: str) -> Dict[str, Any]:
    """
    Load indicator data from JSON file.
    
    Args:
        filepath: Path to JSON file
        
    Returns:
        Parsed JSON data
    """
    with open(filepath, 'r') as f:
        return json.load(f)


def extract_time_series(data: Dict[str, Any], country_filter: Optional[str] = None) -> Dict[str, List[Tuple[int, float]]]:
    """
    Extract time series data grouped by country.
    
    Args:
        data: Full indicator data
        country_filter: Optional country name to filter by
        
    Returns:
        Dictionary mapping country name to list of (year, value) tuples
    """
    records = data.get('data', {}).get('data', [])
    time_series = defaultdict(list)
    
    for record in records:
        country = record.get('country', {}).get('value')
        date = record.get('date')
        value = record.get('value')
        
        if country and date and value is not None:
            if country_filter is None or country == country_filter:
                try:
                    year = int(date)
                    time_series[country].append((year, float(value)))
                except (ValueError, TypeError):
                    continue
    
    # Sort by year
    for country in time_series:
        time_series[country].sort(key=lambda x: x[0])
    
    return dict(time_series)


def calculate_growth_rate(time_series: List[Tuple[int, float]]) -> float:
    """
    Calculate average annual growth rate.
    
    Args:
        time_series: List of (year, value) tuples
        
    Returns:
        Average growth rate as percentage
    """
    if len(time_series) < 2:
        return 0.0
    
    values = [v for _, v in time_series]
    years = [y for y, _ in time_series]
    
    # Calculate year-over-year growth rates
    growth_rates = []
    for i in range(1, len(values)):
        if values[i-1] != 0:
            growth = ((values[i] - values[i-1]) / values[i-1]) * 100
            growth_rates.append(growth)
    
    return statistics.mean(growth_rates) if growth_rates else 0.0


def detect_trend(time_series: List[Tuple[int, float]]) -> str:
    """
    Detect trend direction using simple linear regression.
    
    Args:
        time_series: List of (year, value) tuples
        
    Returns:
        Trend description: "increasing", "decreasing", or "stable"
    """
    if len(time_series) < 3:
        return "insufficient data"
    
    years = np.array([y for y, _ in time_series])
    values = np.array([v for _, v in time_series])
    
    # Simple linear regression
    n = len(years)
    mean_x = np.mean(years)
    mean_y = np.mean(values)
    
    numerator = np.sum((years - mean_x) * (values - mean_y))
    denominator = np.sum((years - mean_x) ** 2)
    
    if denominator == 0:
        return "stable"
    
    slope = numerator / denominator
    
    # Classify trend based on slope
    threshold = np.std(values) * 0.01  # 1% of standard deviation
    
    if slope > threshold:
        return "increasing"
    elif slope < -threshold:
        return "decreasing"
    else:
        return "stable"


def calculate_volatility(time_series: List[Tuple[int, float]]) -> float:
    """
    Calculate volatility (coefficient of variation).
    
    Args:
        time_series: List of (year, value) tuples
        
    Returns:
        Coefficient of variation
    """
    values = [v for _, v in time_series]
    if not values or statistics.mean(values) == 0:
        return 0.0
    
    return (statistics.stdev(values) / statistics.mean(values)) * 100


def simple_forecast(time_series: List[Tuple[int, float]], years_ahead: int = 5) -> List[Tuple[int, float]]:
    """
    Simple linear extrapolation for forecasting.
    
    Args:
        time_series: Historical (year, value) tuples
        years_ahead: Number of years to forecast
        
    Returns:
        List of forecasted (year, value) tuples
    """
    if len(time_series) < 2:
        return []
    
    years = np.array([y for y, _ in time_series])
    values = np.array([v for _, v in time_series])
    
    # Linear regression
    n = len(years)
    mean_x = np.mean(years)
    mean_y = np.mean(values)
    
    numerator = np.sum((years - mean_x) * (values - mean_y))
    denominator = np.sum((years - mean_x) ** 2)
    
    if denominator == 0:
        return []
    
    slope = numerator / denominator
    intercept = mean_y - slope * mean_x
    
    # Generate forecasts
    last_year = int(years[-1])
    forecasts = []
    
    for i in range(1, years_ahead + 1):
        future_year = last_year + i
        forecast_value = slope * future_year + intercept
        forecasts.append((future_year, float(forecast_value)))
    
    return forecasts


def analyze_climate_data(filepath: str, country: Optional[str] = None, top_n: int = 10) -> Dict[str, Any]:
    """
    Comprehensive analysis of a climate/economic indicator file.
    
    Args:
        filepath: Path to JSON data file
        country: Optional specific country to analyze
        top_n: Number of top countries to include in analysis
        
    Returns:
        Dictionary with analysis results
    """
    data = load_indicator_data(filepath)
    indicator = data.get('indicator', 'Unknown')
    time_series_data = extract_time_series(data, country)
    
    analysis = {
        'indicator': indicator,
        'filepath': filepath,
        'total_countries': len(time_series_data),
        'country_analyses': {}
    }
    
    # Analyze each country
    country_summaries = []
    
    for country_name, ts in time_series_data.items():
        if len(ts) < 2:
            continue
        
        latest_year, latest_value = ts[-1]
        earliest_year, earliest_value = ts[0]
        
        country_analysis = {
            'country': country_name,
            'data_points': len(ts),
            'time_range': f"{earliest_year}-{latest_year}",
            'latest_value': latest_value,
            'earliest_value': earliest_value,
            'trend': detect_trend(ts),
            'avg_growth_rate': round(calculate_growth_rate(ts), 2),
            'volatility': round(calculate_volatility(ts), 2),
            'forecast_5yr': simple_forecast(ts, 5)
        }
        
        country_summaries.append(country_analysis)
    
    # Sort by latest value and take top N
    country_summaries.sort(key=lambda x: abs(x['latest_value']), reverse=True)
    
    if country:
        # If specific country requested, filter to that
        analysis['country_analyses'] = {
            c['country']: c for c in country_summaries 
            if c['country'] == country
        }
    else:
        # Otherwise take top N
        analysis['country_analyses'] = {
            c['country']: c for c in country_summaries[:top_n]
        }
    
    # Global summary statistics
    all_latest_values = [c['latest_value'] for c in country_summaries]
    if all_latest_values:
        analysis['global_summary'] = {
            'max_value': max(all_latest_values),
            'min_value': min(all_latest_values),
            'mean_value': round(statistics.mean(all_latest_values), 2),
            'median_value': round(statistics.median(all_latest_values), 2)
        }
    
    return analysis


def print_analysis(analysis: Dict[str, Any]) -> None:
    """
    Pretty print analysis results.
    
    Args:
        analysis: Analysis dictionary from analyze_climate_data
    """
    print("=" * 80)
    print(f"ANALYSIS: {analysis['indicator']}")
    print("=" * 80)
    print(f"Total countries analyzed: {analysis['total_countries']}")
    
    if 'global_summary' in analysis:
        print("\nGlobal Summary:")
        for key, value in analysis['global_summary'].items():
            print(f"  {key}: {value:,.2f}")
    
    print(f"\nTop Countries Analysis:")
    print("-" * 80)
    
    for country, data in analysis['country_analyses'].items():
        print(f"\n{country}:")
        print(f"  Time range: {data['time_range']} ({data['data_points']} data points)")
        print(f"  Latest value: {data['latest_value']:,.2f}")
        print(f"  Trend: {data['trend']}")
        print(f"  Avg growth rate: {data['avg_growth_rate']:.2f}% per year")
        print(f"  Volatility: {data['volatility']:.2f}%")
        
        if data['forecast_5yr']:
            print(f"  5-year forecast:")
            for year, value in data['forecast_5yr']:
                print(f"    {year}: {value:,.2f}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python data_analyzer.py <path_to_json_file> [country_name]")
        print("Example: python data_analyzer.py ../example/files/api_results_SP.POP.TOTL.json")
        print("Example: python data_analyzer.py ../example/files/api_results_SP.POP.TOTL.json 'United States'")
        sys.exit(1)
    
    data_file = sys.argv[1]
    country_filter = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        analysis = analyze_climate_data(data_file, country=country_filter, top_n=10)
        print_analysis(analysis)
        
        # Save to JSON
        output_dir = Path(__file__).parent / "output"
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / f"analysis_{Path(data_file).stem}.json"
        with open(output_file, 'w') as f:
            json.dump(analysis, f, indent=2)
        print(f"\n\nAnalysis saved to: {output_file}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
