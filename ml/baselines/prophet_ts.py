from __future__ import annotations

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
import mlflow
from prophet import Prophet


def fit_prophet_and_forecast(
    series: pd.Series,
    horizon: int,
    seasonality_mode: str = "additive",
    yearly_seasonality: bool = True,
    weekly_seasonality: bool = True,
    daily_seasonality: bool = False,
    changepoint_prior_scale: float = 0.05,
    seasonality_prior_scale: float = 10.0,
    holidays: Optional[pd.DataFrame] = None
) -> pd.DataFrame:
    """
    Fit Prophet model and generate forecasts.
    
    Args:
        series: Time series data
        horizon: Forecast horizon
        seasonality_mode: 'additive' or 'multiplicative'
        yearly_seasonality: Whether to include yearly seasonality
        weekly_seasonality: Whether to include weekly seasonality
        daily_seasonality: Whether to include daily seasonality
        changepoint_prior_scale: Flexibility of trend changes
        seasonality_prior_scale: Strength of seasonality
        holidays: Optional holidays dataframe
    
    Returns:
        DataFrame with columns: step, yhat, yhat_lower, yhat_upper
    """
    with mlflow.start_run(nested=True):
        # Log parameters
        mlflow.log_params({
            "model": "Prophet",
            "horizon": horizon,
            "seasonality_mode": seasonality_mode,
            "yearly_seasonality": yearly_seasonality,
            "weekly_seasonality": weekly_seasonality,
            "daily_seasonality": daily_seasonality,
            "changepoint_prior_scale": changepoint_prior_scale,
            "seasonality_prior_scale": seasonality_prior_scale
        })
        
        # Prepare data for Prophet
        df = pd.DataFrame({
            'ds': pd.date_range(start='2023-01-01', periods=len(series), freq='W'),
            'y': series.values
        })
        
        # Initialize Prophet model
        model = Prophet(
            seasonality_mode=seasonality_mode,
            yearly_seasonality=yearly_seasonality,
            weekly_seasonality=weekly_seasonality,
            daily_seasonality=daily_seasonality,
            changepoint_prior_scale=changepoint_prior_scale,
            seasonality_prior_scale=seasonality_prior_scale
        )
        
        # Add holidays if provided
        if holidays is not None:
            model.add_country_holidays(country_name='US')
        
        # Fit model
        model.fit(df)
        
        # Create future dataframe
        future = model.make_future_dataframe(periods=horizon, freq='W')
        
        # Generate forecast
        forecast = model.predict(future)
        
        # Extract forecast results
        forecast_results = forecast.tail(horizon)
        
        # Log metrics
        mlflow.log_metric("trend_strength", float(forecast_results['trend'].std()))
        mlflow.log_metric("seasonality_strength", float(forecast_results['yearly'].std()))
        
        # Create output DataFrame
        result_df = pd.DataFrame({
            'step': range(1, horizon + 1),
            'yhat': forecast_results['yhat'].values,
            'yhat_lower': forecast_results['yhat_lower'].values,
            'yhat_upper': forecast_results['yhat_upper'].values
        })
        
        return result_df


def create_pharma_holidays() -> pd.DataFrame:
    """Create holidays dataframe for pharma industry."""
    holidays = pd.DataFrame({
        'holiday': [
            'New Year', 'MLK Day', 'Presidents Day', 'Memorial Day',
            'Independence Day', 'Labor Day', 'Columbus Day', 'Veterans Day',
            'Thanksgiving', 'Christmas', 'Black Friday', 'Cyber Monday'
        ],
        'ds': pd.to_datetime([
            '2023-01-01', '2023-01-16', '2023-02-20', '2023-05-29',
            '2023-07-04', '2023-09-04', '2023-10-09', '2023-11-11',
            '2023-11-23', '2023-12-25', '2023-11-24', '2023-11-27'
        ]),
        'lower_window': [0, 0, 0, 0, 0, 0, 0, 0, -1, 0, 0, 0],
        'upper_window': [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
    })
    
    return holidays


def fit_prophet_with_holidays(series: pd.Series, horizon: int) -> pd.DataFrame:
    """Fit Prophet model with pharma-specific holidays."""
    holidays = create_pharma_holidays()
    return fit_prophet_and_forecast(
        series=series,
        horizon=horizon,
        holidays=holidays,
        seasonality_mode="multiplicative",
        yearly_seasonality=True,
        weekly_seasonality=True
    )
