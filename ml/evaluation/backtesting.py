from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Callable, Dict, List, Tuple
import mlflow


def rolling_window_backtest(
    series: pd.Series,
    forecast_func: Callable[[pd.Series, int], pd.DataFrame],
    test_periods: int,
    window_size: int = 52,
    step_size: int = 1,
) -> Tuple[pd.DataFrame, Dict[str, float]]:
    """
    Perform rolling window backtesting on a time series.
    
    Args:
        series: Time series data
        forecast_func: Function that takes (series, horizon) and returns DataFrame with 'yhat'
        test_periods: Number of periods to test
        window_size: Size of training window
        step_size: Step size for rolling window
    
    Returns:
        Tuple of (predictions_df, metrics_dict)
    """
    if len(series) < window_size + test_periods:
        raise ValueError("Series too short for backtesting")
    
    predictions = []
    actuals = []
    
    for i in range(0, test_periods, step_size):
        train_end = len(series) - test_periods + i
        train_start = max(0, train_end - window_size)
        
        train_series = series.iloc[train_start:train_end]
        actual_value = series.iloc[train_end]
        
        # Forecast 1 step ahead
        forecast_df = forecast_func(train_series, 1)
        predicted_value = forecast_df.iloc[0]['yhat']
        
        predictions.append(predicted_value)
        actuals.append(actual_value)
    
    # Create results DataFrame
    results_df = pd.DataFrame({
        'actual': actuals,
        'predicted': predictions,
        'error': np.array(actuals) - np.array(predictions),
        'abs_error': np.abs(np.array(actuals) - np.array(predictions)),
        'pct_error': (np.array(actuals) - np.array(predictions)) / np.array(actuals) * 100
    })
    
    # Calculate metrics
    metrics = calculate_forecast_metrics(np.array(actuals), np.array(predictions))
    
    return results_df, metrics


def calculate_forecast_metrics(actual: np.ndarray, predicted: np.ndarray) -> Dict[str, float]:
    """Calculate standard forecasting metrics."""
    actual = np.asarray(actual)
    predicted = np.asarray(predicted)
    
    # Handle division by zero
    actual_nonzero = actual[actual != 0]
    predicted_nonzero = predicted[actual != 0]
    
    metrics = {}
    
    # Mean Absolute Error
    metrics['mae'] = float(np.mean(np.abs(actual - predicted)))
    
    # Root Mean Square Error
    metrics['rmse'] = float(np.sqrt(np.mean((actual - predicted) ** 2)))
    
    # Mean Absolute Percentage Error
    if len(actual_nonzero) > 0:
        metrics['mape'] = float(np.mean(np.abs((actual_nonzero - predicted_nonzero) / actual_nonzero)) * 100)
    else:
        metrics['mape'] = float('inf')
    
    # Weighted Absolute Percentage Error
    if np.sum(actual) != 0:
        metrics['wape'] = float(np.sum(np.abs(actual - predicted)) / np.sum(actual) * 100)
    else:
        metrics['wape'] = float('inf')
    
    # Bias (mean error)
    metrics['bias'] = float(np.mean(predicted - actual))
    
    # Mean Absolute Scaled Error (naive forecast as benchmark)
    if len(actual) > 1:
        naive_mae = np.mean(np.abs(actual[1:] - actual[:-1]))
        if naive_mae != 0:
            metrics['mase'] = metrics['mae'] / naive_mae
        else:
            metrics['mase'] = float('inf')
    else:
        metrics['mase'] = float('inf')
    
    return metrics


def backtest_model(
    brand_id: str,
    model_name: str,
    forecast_func: Callable[[pd.Series, int], pd.DataFrame],
    test_periods: int = 12,
    window_size: int = 52,
) -> Dict[str, float]:
    """
    Backtest a specific model and log results to MLflow.
    
    Args:
        brand_id: Brand identifier
        model_name: Name of the model being tested
        forecast_func: Forecasting function
        test_periods: Number of periods to test
        window_size: Training window size
    
    Returns:
        Dictionary of metrics
    """
    from ml.utils.data import load_sample_series
    
    with mlflow.start_run(run_name=f"backtest_{model_name}_{brand_id}"):
        # Load data
        series = load_sample_series(brand_id)
        
        # Log parameters
        mlflow.log_params({
            "brand_id": brand_id,
            "model_name": model_name,
            "test_periods": test_periods,
            "window_size": window_size,
            "series_length": len(series)
        })
        
        # Perform backtesting
        results_df, metrics = rolling_window_backtest(
            series, forecast_func, test_periods, window_size
        )
        
        # Log metrics
        mlflow.log_metrics(metrics)
        
        # Save results as artifact
        results_df.to_csv("backtest_results.csv", index=False)
        mlflow.log_artifact("backtest_results.csv")
        
        return metrics
