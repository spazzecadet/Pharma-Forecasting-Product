from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import mlflow


class DriftType(str, Enum):
    DATA_DRIFT = "data_drift"
    CONCEPT_DRIFT = "concept_drift"
    PERFORMANCE_DRIFT = "performance_drift"


@dataclass
class DriftAlert:
    drift_type: DriftType
    severity: str  # "low", "medium", "high", "critical"
    message: str
    detected_at: datetime
    metric_value: float
    threshold: float
    brand_id: str
    model_id: str


class DriftDetector:
    """Detect various types of drift in ML models and data."""
    
    def __init__(self, reference_window: int = 30):
        """
        Initialize drift detector.
        
        Args:
            reference_window: Number of days to use as reference period
        """
        self.reference_window = reference_window
        self.alerts: List[DriftAlert] = []
    
    def detect_data_drift(
        self,
        reference_data: pd.DataFrame,
        current_data: pd.DataFrame,
        brand_id: str,
        model_id: str,
        threshold: float = 0.1
    ) -> List[DriftAlert]:
        """
        Detect data drift using statistical tests.
        
        Args:
            reference_data: Reference dataset
            current_data: Current dataset
            brand_id: Brand identifier
            model_id: Model identifier
            threshold: Drift detection threshold
        
        Returns:
            List of drift alerts
        """
        alerts = []
        
        # Check for missing columns
        missing_cols = set(reference_data.columns) - set(current_data.columns)
        if missing_cols:
            alerts.append(DriftAlert(
                drift_type=DriftType.DATA_DRIFT,
                severity="high",
                message=f"Missing columns: {list(missing_cols)}",
                detected_at=datetime.utcnow(),
                metric_value=1.0,
                threshold=0.0,
                brand_id=brand_id,
                model_id=model_id
            ))
        
        # Check for new columns
        new_cols = set(current_data.columns) - set(reference_data.columns)
        if new_cols:
            alerts.append(DriftAlert(
                drift_type=DriftType.DATA_DRIFT,
                severity="medium",
                message=f"New columns detected: {list(new_cols)}",
                detected_at=datetime.utcnow(),
                metric_value=1.0,
                threshold=0.0,
                brand_id=brand_id,
                model_id=model_id
            ))
        
        # Check numerical columns for distribution drift
        numerical_cols = reference_data.select_dtypes(include=[np.number]).columns
        
        for col in numerical_cols:
            if col in current_data.columns:
                # Kolmogorov-Smirnov test
                from scipy import stats
                
                ref_values = reference_data[col].dropna()
                curr_values = current_data[col].dropna()
                
                if len(ref_values) > 0 and len(curr_values) > 0:
                    ks_stat, p_value = stats.ks_2samp(ref_values, curr_values)
                    
                    if p_value < threshold:
                        severity = "critical" if p_value < 0.001 else "high" if p_value < 0.01 else "medium"
                        
                        alerts.append(DriftAlert(
                            drift_type=DriftType.DATA_DRIFT,
                            severity=severity,
                            message=f"Distribution drift detected in {col} (KS p-value: {p_value:.4f})",
                            detected_at=datetime.utcnow(),
                            metric_value=p_value,
                            threshold=threshold,
                            brand_id=brand_id,
                            model_id=model_id
                        ))
        
        return alerts
    
    def detect_concept_drift(
        self,
        historical_errors: List[float],
        recent_errors: List[float],
        brand_id: str,
        model_id: str,
        threshold: float = 0.05
    ) -> List[DriftAlert]:
        """
        Detect concept drift using error distribution changes.
        
        Args:
            historical_errors: Historical prediction errors
            recent_errors: Recent prediction errors
            brand_id: Brand identifier
            model_id: Model identifier
            threshold: Drift detection threshold
        
        Returns:
            List of drift alerts
        """
        alerts = []
        
        if len(historical_errors) < 10 or len(recent_errors) < 5:
            return alerts
        
        # Mann-Whitney U test for error distributions
        from scipy import stats
        
        u_stat, p_value = stats.mannwhitneyu(historical_errors, recent_errors, alternative='two-sided')
        
        if p_value < threshold:
            # Calculate error increase
            hist_mean = np.mean(historical_errors)
            recent_mean = np.mean(recent_errors)
            error_increase = (recent_mean - hist_mean) / hist_mean if hist_mean > 0 else 0
            
            severity = "critical" if error_increase > 0.5 else "high" if error_increase > 0.2 else "medium"
            
            alerts.append(DriftAlert(
                drift_type=DriftType.CONCEPT_DRIFT,
                severity=severity,
                message=f"Concept drift detected (error increase: {error_increase:.2%})",
                detected_at=datetime.utcnow(),
                metric_value=p_value,
                threshold=threshold,
                brand_id=brand_id,
                model_id=model_id
            ))
        
        return alerts
    
    def detect_performance_drift(
        self,
        historical_metrics: Dict[str, List[float]],
        recent_metrics: Dict[str, List[float]],
        brand_id: str,
        model_id: str,
        threshold: float = 0.1
    ) -> List[DriftAlert]:
        """
        Detect performance drift using metric degradation.
        
        Args:
            historical_metrics: Historical performance metrics
            recent_metrics: Recent performance metrics
            brand_id: Brand identifier
            model_id: Model identifier
            threshold: Performance degradation threshold
        
        Returns:
            List of drift alerts
        """
        alerts = []
        
        for metric_name in historical_metrics:
            if metric_name in recent_metrics:
                hist_values = historical_metrics[metric_name]
                recent_values = recent_metrics[metric_name]
                
                if len(hist_values) > 0 and len(recent_values) > 0:
                    hist_mean = np.mean(hist_values)
                    recent_mean = np.mean(recent_values)
                    
                    # Calculate performance change
                    if metric_name in ['mape', 'wape', 'mae', 'rmse']:
                        # For error metrics, increase is bad
                        performance_change = (recent_mean - hist_mean) / hist_mean if hist_mean > 0 else 0
                    else:
                        # For accuracy metrics, decrease is bad
                        performance_change = (hist_mean - recent_mean) / hist_mean if hist_mean > 0 else 0
                    
                    if performance_change > threshold:
                        severity = "critical" if performance_change > 0.5 else "high" if performance_change > 0.2 else "medium"
                        
                        alerts.append(DriftAlert(
                            drift_type=DriftType.PERFORMANCE_DRIFT,
                            severity=severity,
                            message=f"Performance drift detected in {metric_name} (degradation: {performance_change:.2%})",
                            detected_at=datetime.utcnow(),
                            metric_value=performance_change,
                            threshold=threshold,
                            brand_id=brand_id,
                            model_id=model_id
                        ))
        
        return alerts
    
    def detect_all_drift(
        self,
        reference_data: pd.DataFrame,
        current_data: pd.DataFrame,
        historical_errors: List[float],
        recent_errors: List[float],
        historical_metrics: Dict[str, List[float]],
        recent_metrics: Dict[str, List[float]],
        brand_id: str,
        model_id: str
    ) -> List[DriftAlert]:
        """Detect all types of drift."""
        all_alerts = []
        
        # Data drift
        data_alerts = self.detect_data_drift(reference_data, current_data, brand_id, model_id)
        all_alerts.extend(data_alerts)
        
        # Concept drift
        concept_alerts = self.detect_concept_drift(historical_errors, recent_errors, brand_id, model_id)
        all_alerts.extend(concept_alerts)
        
        # Performance drift
        performance_alerts = self.detect_performance_drift(historical_metrics, recent_metrics, brand_id, model_id)
        all_alerts.extend(performance_alerts)
        
        # Store alerts
        self.alerts.extend(all_alerts)
        
        return all_alerts
    
    def get_drift_summary(self, brand_id: str = None, model_id: str = None) -> Dict[str, Any]:
        """Get summary of drift alerts."""
        filtered_alerts = self.alerts
        
        if brand_id:
            filtered_alerts = [alert for alert in filtered_alerts if alert.brand_id == brand_id]
        
        if model_id:
            filtered_alerts = [alert for alert in filtered_alerts if alert.model_id == model_id]
        
        summary = {
            "total_alerts": len(filtered_alerts),
            "by_type": {},
            "by_severity": {},
            "recent_alerts": []
        }
        
        # Count by type
        for alert in filtered_alerts:
            drift_type = alert.drift_type.value
            summary["by_type"][drift_type] = summary["by_type"].get(drift_type, 0) + 1
            
            severity = alert.severity
            summary["by_severity"][severity] = summary["by_severity"].get(severity, 0) + 1
        
        # Recent alerts (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_alerts = [alert for alert in filtered_alerts if alert.detected_at > week_ago]
        summary["recent_alerts"] = [
            {
                "drift_type": alert.drift_type.value,
                "severity": alert.severity,
                "message": alert.message,
                "detected_at": alert.detected_at.isoformat(),
                "brand_id": alert.brand_id,
                "model_id": alert.model_id
            }
            for alert in recent_alerts
        ]
        
        return summary


class ModelMonitor:
    """Monitor model performance and detect drift."""
    
    def __init__(self):
        self.drift_detector = DriftDetector()
        self.performance_history: Dict[str, List[Dict[str, Any]]] = {}
    
    def log_performance(
        self,
        brand_id: str,
        model_id: str,
        metrics: Dict[str, float],
        timestamp: datetime = None
    ):
        """Log model performance metrics."""
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        key = f"{brand_id}_{model_id}"
        if key not in self.performance_history:
            self.performance_history[key] = []
        
        self.performance_history[key].append({
            "timestamp": timestamp,
            "metrics": metrics
        })
        
        # Keep only last 100 entries
        if len(self.performance_history[key]) > 100:
            self.performance_history[key] = self.performance_history[key][-100:]
    
    def check_drift(self, brand_id: str, model_id: str) -> List[DriftAlert]:
        """Check for drift in a specific model."""
        key = f"{brand_id}_{model_id}"
        
        if key not in self.performance_history:
            return []
        
        history = self.performance_history[key]
        
        if len(history) < 20:
            return []
        
        # Split into historical and recent periods
        split_point = len(history) // 2
        historical = history[:split_point]
        recent = history[split_point:]
        
        # Extract metrics
        historical_metrics = {}
        recent_metrics = {}
        
        for entry in historical:
            for metric, value in entry["metrics"].items():
                if metric not in historical_metrics:
                    historical_metrics[metric] = []
                historical_metrics[metric].append(value)
        
        for entry in recent:
            for metric, value in entry["metrics"].items():
                if metric not in recent_metrics:
                    recent_metrics[metric] = []
                recent_metrics[metric].append(value)
        
        # Detect drift
        alerts = self.drift_detector.detect_performance_drift(
            historical_metrics, recent_metrics, brand_id, model_id
        )
        
        return alerts
    
    def get_performance_trend(self, brand_id: str, model_id: str, metric: str) -> Dict[str, Any]:
        """Get performance trend for a specific metric."""
        key = f"{brand_id}_{model_id}"
        
        if key not in self.performance_history:
            return {"error": "No performance data found"}
        
        history = self.performance_history[key]
        values = [entry["metrics"].get(metric) for entry in history if metric in entry["metrics"]]
        timestamps = [entry["timestamp"] for entry in history if metric in entry["metrics"]]
        
        if len(values) < 2:
            return {"error": "Insufficient data for trend analysis"}
        
        # Calculate trend
        x = np.arange(len(values))
        slope, intercept = np.polyfit(x, values, 1)
        
        # Calculate trend direction
        if slope > 0.01:
            trend = "improving"
        elif slope < -0.01:
            trend = "degrading"
        else:
            trend = "stable"
        
        return {
            "metric": metric,
            "trend": trend,
            "slope": float(slope),
            "current_value": float(values[-1]),
            "average_value": float(np.mean(values)),
            "data_points": len(values)
        }
