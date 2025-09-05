from __future__ import annotations

import os
import mlflow
import pandas as pd
from typing import Dict, Any, Optional
from datetime import datetime


class MLflowTracker:
    """Centralized MLflow tracking for forecast runs and experiments."""
    
    def __init__(self, tracking_uri: str = None):
        if tracking_uri:
            mlflow.set_tracking_uri(tracking_uri)
        elif not mlflow.get_tracking_uri():
            # Default to local file store
            mlflow.set_tracking_uri(f"file://{os.path.abspath('./mlruns')}")
    
    def start_forecast_run(
        self,
        run_id: str,
        brand_id: str,
        model_type: str,
        horizon: int,
        params: Dict[str, Any] = None
    ) -> str:
        """Start a new MLflow run for forecasting."""
        with mlflow.start_run(run_name=f"forecast_{brand_id}_{model_type}_{run_id[:8]}"):
            # Log parameters
            mlflow.log_params({
                "run_id": run_id,
                "brand_id": brand_id,
                "model_type": model_type,
                "horizon": horizon,
                "timestamp": datetime.utcnow().isoformat(),
                **(params or {})
            })
            
            # Set tags
            mlflow.set_tags({
                "task": "forecasting",
                "brand": brand_id,
                "model": model_type,
                "run_type": "forecast"
            })
            
            return mlflow.active_run().info.run_id
    
    def log_forecast_metrics(
        self,
        mlflow_run_id: str,
        metrics: Dict[str, float],
        artifacts: Dict[str, Any] = None
    ):
        """Log metrics and artifacts for a forecast run."""
        with mlflow.start_run(run_id=mlflow_run_id):
            # Log metrics
            mlflow.log_metrics(metrics)
            
            # Log artifacts
            if artifacts:
                for name, data in artifacts.items():
                    if isinstance(data, pd.DataFrame):
                        data.to_csv(f"{name}.csv", index=False)
                        mlflow.log_artifact(f"{name}.csv")
                    elif isinstance(data, str):
                        with open(f"{name}.txt", "w") as f:
                            f.write(data)
                        mlflow.log_artifact(f"{name}.txt")
    
    def start_backtest_run(
        self,
        brand_id: str,
        model_type: str,
        test_periods: int,
        window_size: int,
        params: Dict[str, Any] = None
    ) -> str:
        """Start a new MLflow run for backtesting."""
        with mlflow.start_run(run_name=f"backtest_{brand_id}_{model_type}_{test_periods}w"):
            # Log parameters
            mlflow.log_params({
                "brand_id": brand_id,
                "model_type": model_type,
                "test_periods": test_periods,
                "window_size": window_size,
                "timestamp": datetime.utcnow().isoformat(),
                **(params or {})
            })
            
            # Set tags
            mlflow.set_tags({
                "task": "backtesting",
                "brand": brand_id,
                "model": model_type,
                "run_type": "backtest"
            })
            
            return mlflow.active_run().info.run_id
    
    def log_backtest_results(
        self,
        mlflow_run_id: str,
        metrics: Dict[str, float],
        results_df: pd.DataFrame
    ):
        """Log backtesting results and metrics."""
        with mlflow.start_run(run_id=mlflow_run_id):
            # Log metrics
            mlflow.log_metrics(metrics)
            
            # Log results as artifact
            results_df.to_csv("backtest_results.csv", index=False)
            mlflow.log_artifact("backtest_results.csv")
    
    def get_experiment_runs(
        self,
        experiment_name: str = "Default",
        brand_id: str = None,
        model_type: str = None
    ) -> pd.DataFrame:
        """Get runs from an experiment with optional filters."""
        try:
            experiment = mlflow.get_experiment_by_name(experiment_name)
            if not experiment:
                return pd.DataFrame()
            
            runs = mlflow.search_runs(
                experiment_ids=[experiment.experiment_id],
                filter_string=f"tags.brand = '{brand_id}'" if brand_id else None
            )
            
            if model_type:
                runs = runs[runs['tags.model'] == model_type]
            
            return runs
        except Exception:
            return pd.DataFrame()
    
    def compare_models(
        self,
        brand_id: str,
        experiment_name: str = "Default"
    ) -> Dict[str, Any]:
        """Compare model performance for a brand."""
        runs = self.get_experiment_runs(experiment_name, brand_id)
        
        if runs.empty:
            return {"error": "No runs found"}
        
        # Group by model type and calculate average metrics
        model_comparison = {}
        for model_type in runs['tags.model'].unique():
            model_runs = runs[runs['tags.model'] == model_type]
            
            # Calculate average metrics
            metrics = ['metrics.mape', 'metrics.wape', 'metrics.mae', 'metrics.rmse']
            avg_metrics = {}
            for metric in metrics:
                if metric in model_runs.columns:
                    avg_metrics[metric.split('.')[1]] = model_runs[metric].mean()
            
            model_comparison[model_type] = {
                "runs_count": len(model_runs),
                "avg_metrics": avg_metrics,
                "best_run_id": model_runs.loc[model_runs['metrics.mape'].idxmin(), 'run_id']
            }
        
        return model_comparison


# Global tracker instance
tracker = MLflowTracker()
