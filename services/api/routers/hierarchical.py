from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
import numpy as np
import sys
from pathlib import Path

from auth.dependencies import get_current_user, require_permission
from auth.models import User

router = APIRouter(prefix="/hierarchical", tags=["hierarchical"])

# Add repo root to path for ML imports
repo_root = Path(__file__).resolve().parents[3]
if str(repo_root) not in sys.path:
    sys.path.append(str(repo_root))

from ml.hierarchical.reconciliation import HierarchicalReconciler, ReconciliationMethod, create_pharma_hierarchy  # type: ignore


class HierarchicalForecastRequest(BaseModel):
    brand_hierarchy: Dict[str, List[str]] = Field(..., description="Brand hierarchy structure")
    geo_hierarchy: Dict[str, List[str]] = Field(..., description="Geography hierarchy structure")
    method: ReconciliationMethod = Field(default=ReconciliationMethod.BOTTOM_UP, description="Reconciliation method")
    horizon: int = Field(..., gt=0, le=104, description="Forecast horizon")


class HierarchicalForecastResult(BaseModel):
    reconciled_forecasts: Dict[str, List[float]] = Field(..., description="Reconciled forecasts by node")
    method: ReconciliationMethod = Field(..., description="Reconciliation method used")
    hierarchy_levels: List[List[str]] = Field(..., description="Hierarchy levels")
    accuracy_metrics: Optional[Dict[str, Dict[str, float]]] = None


@router.post("/forecast", response_model=HierarchicalForecastResult)
def create_hierarchical_forecast(
    request: HierarchicalForecastRequest,
    current_user: User = Depends(require_permission("forecasts", "write"))
):
    """Create hierarchical forecasts with reconciliation."""
    try:
        # Create hierarchy reconciler
        reconciler = HierarchicalReconciler(request.brand_hierarchy)
        
        # Generate individual forecasts for each node
        # In practice, this would call the actual forecasting models
        forecasts = {}
        for parent, children in request.brand_hierarchy.items():
            # Mock forecast for parent
            forecasts[parent] = np.random.normal(1000, 100, request.horizon)
            
            # Mock forecasts for children
            for child in children:
                forecasts[child] = np.random.normal(200, 50, request.horizon)
        
        # Reconcile forecasts
        reconciled = reconciler.reconcile_forecasts(
            forecasts,
            method=request.method
        )
        
        # Convert to response format
        reconciled_forecasts = {
            node: forecast.tolist() for node, forecast in reconciled.items()
        }
        
        return HierarchicalForecastResult(
            reconciled_forecasts=reconciled_forecasts,
            method=request.method,
            hierarchy_levels=reconciler.levels
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hierarchical forecasting failed: {str(e)}")


@router.get("/pharma-hierarchy")
def get_pharma_hierarchy(current_user: User = Depends(require_permission("forecasts", "read"))):
    """Get the default pharma hierarchy structure."""
    reconciler = create_pharma_hierarchy()
    return {
        "hierarchy": reconciler.hierarchy,
        "levels": reconciler.levels
    }


@router.post("/reconcile")
def reconcile_existing_forecasts(
    forecasts: Dict[str, List[float]],
    method: ReconciliationMethod = ReconciliationMethod.BOTTOM_UP,
    current_user: User = Depends(require_permission("forecasts", "write"))
):
    """Reconcile existing forecasts using specified method."""
    try:
        # Convert to numpy arrays
        np_forecasts = {node: np.array(forecast) for node, forecast in forecasts.items()}
        
        # Create a simple hierarchy for demonstration
        hierarchy = {
            "Total": [node for node in forecasts.keys() if not node.startswith("Brand_")],
            "Brand_A": [node for node in forecasts.keys() if node.startswith("Brand_A")],
            "Brand_B": [node for node in forecasts.keys() if node.startswith("Brand_B")],
        }
        
        reconciler = HierarchicalReconciler(hierarchy)
        reconciled = reconciler.reconcile_forecasts(np_forecasts, method=method)
        
        return {
            "reconciled_forecasts": {node: forecast.tolist() for node, forecast in reconciled.items()},
            "method": method.value
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reconciliation failed: {str(e)}")


@router.get("/methods")
def get_reconciliation_methods(current_user: User = Depends(require_permission("forecasts", "read"))):
    """Get available reconciliation methods."""
    return {
        "methods": [
            {
                "name": "bottom_up",
                "description": "Aggregate bottom-level forecasts up the hierarchy",
                "use_case": "When bottom-level data is most reliable"
            },
            {
                "name": "top_down",
                "description": "Distribute top-level forecasts down the hierarchy",
                "use_case": "When top-level forecasts are most accurate"
            },
            {
                "name": "middle_out",
                "description": "Start from middle level and reconcile both ways",
                "use_case": "When middle-level forecasts are most reliable"
            },
            {
                "name": "mint",
                "description": "Minimum Trace reconciliation using error variances",
                "use_case": "When you have historical error information"
            }
        ]
    }
