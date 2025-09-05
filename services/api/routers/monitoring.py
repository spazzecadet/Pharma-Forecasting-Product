from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import sys
from pathlib import Path

from auth.dependencies import get_current_user, require_permission
from auth.models import User

router = APIRouter(prefix="/monitoring", tags=["monitoring"])

# Add repo root to path for ML imports
repo_root = Path(__file__).resolve().parents[3]
if str(repo_root) not in sys.path:
    sys.path.append(str(repo_root))

from ml.monitoring.drift_detection import ModelMonitor, DriftAlert, DriftType  # type: ignore

# Global monitor instance
monitor = ModelMonitor()


class PerformanceLogRequest(BaseModel):
    brand_id: str = Field(..., description="Brand identifier")
    model_id: str = Field(..., description="Model identifier")
    metrics: Dict[str, float] = Field(..., description="Performance metrics")
    timestamp: Optional[datetime] = Field(default=None, description="Timestamp (defaults to now)")


class DriftCheckResponse(BaseModel):
    brand_id: str
    model_id: str
    alerts: List[Dict[str, Any]]
    summary: Dict[str, Any]


@router.post("/performance/log")
def log_performance(
    request: PerformanceLogRequest,
    current_user: User = Depends(require_permission("models", "write"))
):
    """Log model performance metrics for monitoring."""
    try:
        monitor.log_performance(
            brand_id=request.brand_id,
            model_id=request.model_id,
            metrics=request.metrics,
            timestamp=request.timestamp
        )
        
        return {"message": "Performance logged successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to log performance: {str(e)}")


@router.get("/drift/check/{brand_id}/{model_id}", response_model=DriftCheckResponse)
def check_drift(
    brand_id: str,
    model_id: str,
    current_user: User = Depends(require_permission("models", "read"))
):
    """Check for drift in a specific model."""
    try:
        alerts = monitor.check_drift(brand_id, model_id)
        
        # Convert alerts to response format
        alert_dicts = []
        for alert in alerts:
            alert_dicts.append({
                "drift_type": alert.drift_type.value,
                "severity": alert.severity,
                "message": alert.message,
                "detected_at": alert.detected_at.isoformat(),
                "metric_value": alert.metric_value,
                "threshold": alert.threshold
            })
        
        # Get drift summary
        summary = monitor.drift_detector.get_drift_summary(brand_id, model_id)
        
        return DriftCheckResponse(
            brand_id=brand_id,
            model_id=model_id,
            alerts=alert_dicts,
            summary=summary
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check drift: {str(e)}")


@router.get("/drift/summary")
def get_drift_summary(
    brand_id: Optional[str] = None,
    model_id: Optional[str] = None,
    current_user: User = Depends(require_permission("models", "read"))
):
    """Get overall drift summary."""
    try:
        summary = monitor.drift_detector.get_drift_summary(brand_id, model_id)
        return summary
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get drift summary: {str(e)}")


@router.get("/performance/trend/{brand_id}/{model_id}/{metric}")
def get_performance_trend(
    brand_id: str,
    model_id: str,
    metric: str,
    current_user: User = Depends(require_permission("models", "read"))
):
    """Get performance trend for a specific metric."""
    try:
        trend = monitor.get_performance_trend(brand_id, model_id, metric)
        return trend
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance trend: {str(e)}")


@router.get("/alerts")
def get_alerts(
    brand_id: Optional[str] = None,
    model_id: Optional[str] = None,
    severity: Optional[str] = None,
    drift_type: Optional[str] = None,
    days: int = 7,
    current_user: User = Depends(require_permission("models", "read"))
):
    """Get drift alerts with optional filters."""
    try:
        all_alerts = monitor.drift_detector.alerts
        
        # Apply filters
        filtered_alerts = all_alerts
        
        if brand_id:
            filtered_alerts = [alert for alert in filtered_alerts if alert.brand_id == brand_id]
        
        if model_id:
            filtered_alerts = [alert for alert in filtered_alerts if alert.model_id == model_id]
        
        if severity:
            filtered_alerts = [alert for alert in filtered_alerts if alert.severity == severity]
        
        if drift_type:
            filtered_alerts = [alert for alert in filtered_alerts if alert.drift_type.value == drift_type]
        
        # Filter by date
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        filtered_alerts = [alert for alert in filtered_alerts if alert.detected_at > cutoff_date]
        
        # Convert to response format
        alert_dicts = []
        for alert in filtered_alerts:
            alert_dicts.append({
                "drift_type": alert.drift_type.value,
                "severity": alert.severity,
                "message": alert.message,
                "detected_at": alert.detected_at.isoformat(),
                "metric_value": alert.metric_value,
                "threshold": alert.threshold,
                "brand_id": alert.brand_id,
                "model_id": alert.model_id
            })
        
        return {
            "alerts": alert_dicts,
            "total_count": len(alert_dicts),
            "filters": {
                "brand_id": brand_id,
                "model_id": model_id,
                "severity": severity,
                "drift_type": drift_type,
                "days": days
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")


@router.get("/health")
def monitoring_health_check(current_user: User = Depends(require_permission("models", "read"))):
    """Health check for monitoring services."""
    try:
        # Check if monitor is working
        summary = monitor.drift_detector.get_drift_summary()
        
        return {
            "status": "healthy",
            "monitor_status": "active",
            "total_alerts": summary["total_alerts"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
