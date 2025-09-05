import uuid
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from models import ForecastPoint, ModelType

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


class ScenarioVariable(BaseModel):
    name: str = Field(..., description="Variable name (e.g., 'price', 'coverage')")
    baseline_value: float = Field(..., description="Current/baseline value")
    scenario_value: float = Field(..., description="What-if scenario value")
    impact_factor: float = Field(default=1.0, description="Impact multiplier on demand")


class ScenarioRequest(BaseModel):
    brand_id: str = Field(..., description="Brand identifier")
    model_type: ModelType = Field(..., description="Base model to use")
    horizon: int = Field(..., gt=0, le=104, description="Forecast horizon")
    variables: List[ScenarioVariable] = Field(..., description="Scenario variables")
    description: Optional[str] = Field(None, description="Scenario description")


class ScenarioComparison(BaseModel):
    step: int
    baseline_yhat: float
    scenario_yhat: float
    delta: float
    delta_pct: float


class ScenarioResult(BaseModel):
    scenario_id: str
    brand_id: str
    model_type: ModelType
    horizon: int
    description: Optional[str]
    baseline_forecast: List[ForecastPoint]
    scenario_forecast: List[ForecastPoint]
    comparison: List[ScenarioComparison]
    total_impact: Dict[str, float]  # Total volume and percentage impact


# In-memory storage
scenarios_db: Dict[str, ScenarioResult] = {}


@router.post("/", response_model=ScenarioResult)
def create_scenario(req: ScenarioRequest):
    """Create and execute a what-if scenario analysis."""
    import sys
    from pathlib import Path
    import numpy as np
    
    # Add repo root to path
    repo_root = Path(__file__).resolve().parents[3]
    if str(repo_root) not in sys.path:
        sys.path.append(str(repo_root))
    
    try:
        from ml.utils.data import load_sample_series  # type: ignore
        from ml.baselines.arima import fit_arima_and_forecast  # type: ignore
        from ml.baselines.xgboost_ts import fit_xgb_and_forecast  # type: ignore
        
        scenario_id = str(uuid.uuid4())
        
        # Get baseline forecast
        series = load_sample_series(req.brand_id)
        
        if req.model_type == ModelType.ARIMA:
            baseline_df = fit_arima_and_forecast(series, req.horizon)
        elif req.model_type == ModelType.XGBOOST:
            baseline_df = fit_xgb_and_forecast(series, req.horizon)
        else:
            raise HTTPException(status_code=400, detail="Unsupported model type")
        
        baseline_forecast = [
            ForecastPoint(step=int(row.step), yhat=float(row.yhat))
            for row in baseline_df.itertuples(index=False)
        ]
        
        # Calculate scenario impact
        # Simple simulation: apply cumulative impact factors
        total_impact_factor = 1.0
        for var in req.variables:
            # Calculate impact based on percentage change
            pct_change = (var.scenario_value - var.baseline_value) / var.baseline_value
            impact = pct_change * var.impact_factor
            total_impact_factor *= (1 + impact)
        
        # Apply impact to baseline forecast
        scenario_forecast = [
            ForecastPoint(
                step=point.step,
                yhat=point.yhat * total_impact_factor,
                yhat_lower=point.yhat_lower * total_impact_factor if point.yhat_lower else None,
                yhat_upper=point.yhat_upper * total_impact_factor if point.yhat_upper else None
            )
            for point in baseline_forecast
        ]
        
        # Create comparison
        comparison = []
        for baseline, scenario in zip(baseline_forecast, scenario_forecast):
            delta = scenario.yhat - baseline.yhat
            delta_pct = (delta / baseline.yhat) * 100 if baseline.yhat != 0 else 0.0
            
            comparison.append(ScenarioComparison(
                step=baseline.step,
                baseline_yhat=baseline.yhat,
                scenario_yhat=scenario.yhat,
                delta=delta,
                delta_pct=delta_pct
            ))
        
        # Calculate total impact
        baseline_total = sum(p.yhat for p in baseline_forecast)
        scenario_total = sum(p.yhat for p in scenario_forecast)
        total_delta = scenario_total - baseline_total
        total_delta_pct = (total_delta / baseline_total) * 100 if baseline_total != 0 else 0.0
        
        total_impact = {
            "baseline_total": baseline_total,
            "scenario_total": scenario_total,
            "absolute_delta": total_delta,
            "percentage_delta": total_delta_pct
        }
        
        # Create result
        result = ScenarioResult(
            scenario_id=scenario_id,
            brand_id=req.brand_id,
            model_type=req.model_type,
            horizon=req.horizon,
            description=req.description,
            baseline_forecast=baseline_forecast,
            scenario_forecast=scenario_forecast,
            comparison=comparison,
            total_impact=total_impact
        )
        
        scenarios_db[scenario_id] = result
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scenario creation failed: {str(e)}")


@router.get("/", response_model=List[str])
def list_scenarios(brand_id: str = None):
    """List scenario IDs with optional brand filter."""
    scenarios = list(scenarios_db.values())
    if brand_id:
        scenarios = [s for s in scenarios if s.brand_id == brand_id]
    return [s.scenario_id for s in scenarios]


@router.get("/{scenario_id}", response_model=ScenarioResult)
def get_scenario(scenario_id: str):
    """Get a specific scenario result."""
    if scenario_id not in scenarios_db:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenarios_db[scenario_id]


@router.delete("/{scenario_id}")
def delete_scenario(scenario_id: str):
    """Delete a scenario."""
    if scenario_id not in scenarios_db:
        raise HTTPException(status_code=404, detail="Scenario not found")
    del scenarios_db[scenario_id]
    return {"message": "Scenario deleted successfully"}


@router.post("/quick-price-test")
def quick_price_scenario(
    brand_id: str,
    baseline_price: float,
    scenario_price: float,
    price_elasticity: float = -0.5,
    horizon: int = 12
):
    """Quick price scenario test with configurable elasticity."""
    pct_change = (scenario_price - baseline_price) / baseline_price
    demand_impact = pct_change * price_elasticity  # Negative elasticity
    
    req = ScenarioRequest(
        brand_id=brand_id,
        model_type=ModelType.ARIMA,
        horizon=horizon,
        variables=[
            ScenarioVariable(
                name="price",
                baseline_value=baseline_price,
                scenario_value=scenario_price,
                impact_factor=demand_impact
            )
        ],
        description=f"Price change from ${baseline_price:.2f} to ${scenario_price:.2f}"
    )
    
    return create_scenario(req)
