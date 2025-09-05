from dagster import Definitions, job, op, schedule, sensor, RunRequest, SkipReason
from dagster import AssetMaterialization, AssetKey
import os
import mlflow
from datetime import datetime, timedelta
from typing import List
import pandas as pd

# Add repo root to path
import sys
from pathlib import Path
repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.append(str(repo_root))

from ml.utils.data import load_sample_series
from ml.baselines.arima import fit_arima_and_forecast
from ml.baselines.xgboost_ts import fit_xgb_and_forecast
from ml.baselines.prophet_ts import fit_prophet_and_forecast
from ml.evaluation.backtesting import backtest_model
from ml.hierarchical.reconciliation import create_pharma_hierarchy


@op
def load_data_op():
    """Load sample data for processing."""
    series = load_sample_series("BRAND_A")
    return series


@op
def run_arima_forecast_op(series):
    """Run ARIMA forecast."""
    if not mlflow.get_tracking_uri():
        mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", f"file://{os.path.abspath('./mlruns')}"))
    
    forecast_df = fit_arima_and_forecast(series, horizon=12)
    
    # Log as asset
    yield AssetMaterialization(
        asset_key=AssetKey("arima_forecast"),
        description="ARIMA forecast results",
        metadata={"rows": len(forecast_df), "columns": list(forecast_df.columns)}
    )
    
    return forecast_df


@op
def run_xgboost_forecast_op(series):
    """Run XGBoost forecast."""
    if not mlflow.get_tracking_uri():
        mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", f"file://{os.path.abspath('./mlruns')}"))
    
    forecast_df = fit_xgb_and_forecast(series, horizon=12)
    
    # Log as asset
    yield AssetMaterialization(
        asset_key=AssetKey("xgboost_forecast"),
        description="XGBoost forecast results",
        metadata={"rows": len(forecast_df), "columns": list(forecast_df.columns)}
    )
    
    return forecast_df


@op
def run_prophet_forecast_op(series):
    """Run Prophet forecast."""
    if not mlflow.get_tracking_uri():
        mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", f"file://{os.path.abspath('./mlruns')}"))
    
    forecast_df = fit_prophet_and_forecast(series, horizon=12)
    
    # Log as asset
    yield AssetMaterialization(
        asset_key=AssetKey("prophet_forecast"),
        description="Prophet forecast results",
        metadata={"rows": len(forecast_df), "columns": list(forecast_df.columns)}
    )
    
    return forecast_df


@op
def run_backtest_op(series):
    """Run backtesting for all models."""
    if not mlflow.get_tracking_uri():
        mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", f"file://{os.path.abspath('./mlruns')}"))
    
    # Backtest ARIMA
    arima_metrics = backtest_model(
        brand_id="BRAND_A",
        model_name="arima",
        forecast_func=lambda series, horizon: fit_arima_and_forecast(series, horizon),
        test_periods=12,
        window_size=52
    )
    
    # Backtest XGBoost
    xgb_metrics = backtest_model(
        brand_id="BRAND_A",
        model_name="xgboost",
        forecast_func=lambda series, horizon: fit_xgb_and_forecast(series, horizon),
        test_periods=12,
        window_size=52
    )
    
    # Log as asset
    yield AssetMaterialization(
        asset_key=AssetKey("backtest_results"),
        description="Backtesting results for all models",
        metadata={
            "arima_mape": arima_metrics.get("mape", 0),
            "xgboost_mape": xgb_metrics.get("mape", 0)
        }
    )
    
    return {"arima": arima_metrics, "xgboost": xgb_metrics}


@op
def run_hierarchical_forecast_op(arima_forecast, xgb_forecast, prophet_forecast):
    """Run hierarchical forecasting and reconciliation."""
    if not mlflow.get_tracking_uri():
        mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", f"file://{os.path.abspath('./mlruns')}"))
    
    # Create hierarchy
    reconciler = create_pharma_hierarchy()
    
    # Prepare forecasts for reconciliation
    forecasts = {
        "Brand_A": arima_forecast["yhat"].values,
        "Brand_A_US": arima_forecast["yhat"].values * 0.6,
        "Brand_A_CA": arima_forecast["yhat"].values * 0.3,
        "Brand_A_UK": arima_forecast["yhat"].values * 0.1,
    }
    
    # Reconcile forecasts
    reconciled = reconciler.reconcile_forecasts(forecasts)
    
    # Log as asset
    yield AssetMaterialization(
        asset_key=AssetKey("hierarchical_forecast"),
        description="Hierarchical reconciled forecasts",
        metadata={"nodes": len(reconciled)}
    )
    
    return reconciled


@job
def daily_forecast_job():
    """Daily forecasting job that runs all models."""
    series = load_data_op()
    arima_forecast = run_arima_forecast_op(series)
    xgb_forecast = run_xgboost_forecast_op(series)
    prophet_forecast = run_prophet_forecast_op(series)
    backtest_results = run_backtest_op(series)
    hierarchical_forecast = run_hierarchical_forecast_op(arima_forecast, xgb_forecast, prophet_forecast)


@job
def weekly_backtest_job():
    """Weekly backtesting job."""
    series = load_data_op()
    run_backtest_op(series)


@schedule(cron="0 6 * * *", job=daily_forecast_job)
def daily_forecast_schedule():
    """Schedule daily forecasts at 6 AM."""
    return {}


@schedule(cron="0 2 * * 1", job=weekly_backtest_job)
def weekly_backtest_schedule():
    """Schedule weekly backtesting on Mondays at 2 AM."""
    return {}


@sensor(job=daily_forecast_job)
def data_quality_sensor():
    """Sensor that triggers when data quality issues are detected."""
    # In practice, this would check data quality metrics
    # For now, we'll skip this sensor
    return SkipReason("Data quality sensor not implemented")


defs = Definitions(
    jobs=[daily_forecast_job, weekly_backtest_job],
    schedules=[daily_forecast_schedule, weekly_backtest_schedule],
    sensors=[data_quality_sensor]
)

