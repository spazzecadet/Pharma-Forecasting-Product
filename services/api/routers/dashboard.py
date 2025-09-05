from fastapi import APIRouter, HTTPException
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import sys
from pathlib import Path
import pandas as pd

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# Add repo root to path for MLflow imports
repo_root = Path(__file__).resolve().parents[3]
if str(repo_root) not in sys.path:
    sys.path.append(str(repo_root))

from ml.experiment_tracking import tracker  # type: ignore


class BrandMetrics(BaseModel):
    brand_id: str
    total_runs: int
    successful_runs: int
    avg_mape: Optional[float] = None
    last_forecast_date: Optional[datetime] = None
    forecast_accuracy_trend: List[Dict[str, float]] = Field(default_factory=list)


class PortfolioOverview(BaseModel):
    total_brands: int
    total_runs: int
    successful_runs: int
    avg_accuracy: float
    top_performing_brand: Optional[str] = None
    recent_activity: List[Dict[str, str]] = Field(default_factory=list)


class AccuracyMetrics(BaseModel):
    brand_id: str
    model_type: str
    mape: float
    wape: float
    mae: float
    rmse: float
    bias: float
    run_date: datetime


@router.get("/portfolio", response_model=PortfolioOverview)
def get_portfolio_overview():
    """Get executive portfolio overview."""
    try:
        # Get all runs from MLflow
        runs_df = tracker.get_experiment_runs()
        
        if runs_df.empty:
            return PortfolioOverview(
                total_brands=0,
                total_runs=0,
                successful_runs=0,
                avg_accuracy=0.0
            )
        
        # Calculate metrics
        total_runs = len(runs_df)
        successful_runs = len(runs_df[runs_df['status'] == 'FINISHED'])
        
        # Get unique brands
        brands = runs_df['tags.brand'].unique() if 'tags.brand' in runs_df.columns else []
        total_brands = len(brands)
        
        # Calculate average accuracy (MAPE)
        if 'metrics.mape' in runs_df.columns:
            avg_accuracy = runs_df['metrics.mape'].mean()
            
            # Find top performing brand
            brand_metrics = runs_df.groupby('tags.brand')['metrics.mape'].mean()
            top_performing_brand = brand_metrics.idxmin() if not brand_metrics.empty else None
        else:
            avg_accuracy = 0.0
            top_performing_brand = None
        
        # Recent activity (last 5 runs)
        recent_runs = runs_df.nlargest(5, 'start_time')
        recent_activity = []
        for _, run in recent_runs.iterrows():
            recent_activity.append({
                "run_id": run['run_id'],
                "brand": run.get('tags.brand', 'Unknown'),
                "model": run.get('tags.model', 'Unknown'),
                "status": run.get('status', 'Unknown'),
                "date": run.get('start_time', '').strftime('%Y-%m-%d %H:%M') if pd.notna(run.get('start_time')) else 'Unknown'
            })
        
        return PortfolioOverview(
            total_brands=total_brands,
            total_runs=total_runs,
            successful_runs=successful_runs,
            avg_accuracy=avg_accuracy,
            top_performing_brand=top_performing_brand,
            recent_activity=recent_activity
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get portfolio overview: {str(e)}")


@router.get("/brands/{brand_id}/metrics", response_model=BrandMetrics)
def get_brand_metrics(brand_id: str):
    """Get detailed metrics for a specific brand."""
    try:
        # Get runs for this brand
        runs_df = tracker.get_experiment_runs(brand_id=brand_id)
        
        if runs_df.empty:
            return BrandMetrics(
                brand_id=brand_id,
                total_runs=0,
                successful_runs=0
            )
        
        total_runs = len(runs_df)
        successful_runs = len(runs_df[runs_df['status'] == 'FINISHED'])
        
        # Calculate average MAPE
        avg_mape = None
        if 'metrics.mape' in runs_df.columns:
            avg_mape = runs_df['metrics.mape'].mean()
        
        # Last forecast date
        last_forecast_date = None
        if 'start_time' in runs_df.columns:
            last_run = runs_df.loc[runs_df['start_time'].idxmax()]
            last_forecast_date = last_run['start_time']
        
        # Accuracy trend (last 10 runs)
        trend_runs = runs_df.nlargest(10, 'start_time')
        forecast_accuracy_trend = []
        for _, run in trend_runs.iterrows():
            if 'metrics.mape' in run and pd.notna(run['metrics.mape']):
                forecast_accuracy_trend.append({
                    "date": run['start_time'].strftime('%Y-%m-%d') if pd.notna(run['start_time']) else 'Unknown',
                    "mape": float(run['metrics.mape']),
                    "model": run.get('tags.model', 'Unknown')
                })
        
        return BrandMetrics(
            brand_id=brand_id,
            total_runs=total_runs,
            successful_runs=successful_runs,
            avg_mape=avg_mape,
            last_forecast_date=last_forecast_date,
            forecast_accuracy_trend=forecast_accuracy_trend
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get brand metrics: {str(e)}")


@router.get("/accuracy", response_model=List[AccuracyMetrics])
def get_accuracy_metrics(brand_id: str = None, model_type: str = None):
    """Get accuracy metrics for runs with optional filters."""
    try:
        runs_df = tracker.get_experiment_runs(brand_id=brand_id)
        
        if runs_df.empty:
            return []
        
        # Filter by model type if specified
        if model_type and 'tags.model' in runs_df.columns:
            runs_df = runs_df[runs_df['tags.model'] == model_type]
        
        # Convert to response format
        metrics = []
        for _, run in runs_df.iterrows():
            if all(key in run for key in ['metrics.mape', 'metrics.wape', 'metrics.mae', 'metrics.rmse', 'metrics.bias']):
                metrics.append(AccuracyMetrics(
                    brand_id=run.get('tags.brand', 'Unknown'),
                    model_type=run.get('tags.model', 'Unknown'),
                    mape=float(run['metrics.mape']),
                    wape=float(run['metrics.wape']),
                    mae=float(run['metrics.mae']),
                    rmse=float(run['metrics.rmse']),
                    bias=float(run['metrics.bias']),
                    run_date=run.get('start_time', datetime.utcnow())
                ))
        
        return metrics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get accuracy metrics: {str(e)}")


@router.get("/model-comparison")
def get_model_comparison(brand_id: str):
    """Compare model performance for a brand."""
    try:
        comparison = tracker.compare_models(brand_id)
        return comparison
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get model comparison: {str(e)}")


@router.get("/health-check")
def dashboard_health_check():
    """Health check for dashboard services."""
    try:
        # Check MLflow connection
        runs_df = tracker.get_experiment_runs()
        mlflow_status = "connected" if not runs_df.empty else "no_data"
        
        return {
            "status": "healthy",
            "mlflow": mlflow_status,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
