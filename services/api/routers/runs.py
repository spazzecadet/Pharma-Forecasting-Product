import uuid
from datetime import datetime
from typing import Dict, List

from fastapi import APIRouter, HTTPException
from models import (
    CreateRunRequest,
    ForecastRun,
    ForecastResult,
    ModelType,
    RunStatus,
    ForecastPoint,
)

router = APIRouter(prefix="/runs", tags=["runs"])

# In-memory storage (replace with database in production)
runs_db: Dict[str, ForecastRun] = {}
results_db: Dict[str, ForecastResult] = {}


@router.post("/", response_model=ForecastRun)
def create_run(req: CreateRunRequest):
    """Create a new forecast run."""
    run_id = str(uuid.uuid4())
    run = ForecastRun(
        run_id=run_id,
        brand_id=req.brand_id,
        model_type=req.model_type,
        horizon=req.horizon,
        params=req.params,
    )
    runs_db[run_id] = run
    return run


@router.get("/", response_model=List[ForecastRun])
def list_runs(brand_id: str = None, status: RunStatus = None):
    """List forecast runs with optional filters."""
    runs = list(runs_db.values())
    if brand_id:
        runs = [r for r in runs if r.brand_id == brand_id]
    if status:
        runs = [r for r in runs if r.status == status]
    return sorted(runs, key=lambda x: x.created_at, reverse=True)


@router.get("/{run_id}", response_model=ForecastRun)
def get_run(run_id: str):
    """Get a specific forecast run."""
    if run_id not in runs_db:
        raise HTTPException(status_code=404, detail="Run not found")
    return runs_db[run_id]


@router.post("/{run_id}/execute", response_model=ForecastResult)
def execute_run(run_id: str):
    """Execute a forecast run and return results."""
    if run_id not in runs_db:
        raise HTTPException(status_code=404, detail="Run not found")
    
    run = runs_db[run_id]
    if run.status != RunStatus.PENDING:
        raise HTTPException(status_code=400, detail="Run already executed")
    
    # Update status
    run.status = RunStatus.RUNNING
    runs_db[run_id] = run
    
    try:
        # Execute the forecast based on model type
        if run.model_type == ModelType.ARIMA:
            points = _execute_arima_forecast(run)
        elif run.model_type == ModelType.XGBOOST:
            points = _execute_xgboost_forecast(run)
        else:
            raise HTTPException(status_code=400, detail="Unsupported model type")
        
        # Create result
        result = ForecastResult(
            run_id=run_id,
            brand_id=run.brand_id,
            model_type=run.model_type,
            horizon=run.horizon,
            points=points,
        )
        results_db[run_id] = result
        
        # Update run status
        run.status = RunStatus.COMPLETED
        run.completed_at = datetime.utcnow()
        runs_db[run_id] = run
        
        return result
        
    except Exception as e:
        run.status = RunStatus.FAILED
        runs_db[run_id] = run
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")


@router.get("/{run_id}/result", response_model=ForecastResult)
def get_run_result(run_id: str):
    """Get the result of a completed forecast run."""
    if run_id not in results_db:
        raise HTTPException(status_code=404, detail="Result not found")
    return results_db[run_id]


def _execute_arima_forecast(run: ForecastRun) -> List[ForecastPoint]:
    """Execute ARIMA forecast with lazy imports."""
    import sys
    from pathlib import Path
    
    repo_root = Path(__file__).resolve().parents[3]
    if str(repo_root) not in sys.path:
        sys.path.append(str(repo_root))
    
    from ml.utils.data import load_sample_series  # type: ignore
    from ml.baselines.arima import fit_arima_and_forecast  # type: ignore
    
    series = load_sample_series(run.brand_id)
    forecast_df = fit_arima_and_forecast(series, horizon=run.horizon)
    
    return [
        ForecastPoint(step=int(row.step), yhat=float(row.yhat))
        for row in forecast_df.itertuples(index=False)
    ]


def _execute_xgboost_forecast(run: ForecastRun) -> List[ForecastPoint]:
    """Execute XGBoost forecast with lazy imports."""
    import sys
    from pathlib import Path
    
    repo_root = Path(__file__).resolve().parents[3]
    if str(repo_root) not in sys.path:
        sys.path.append(str(repo_root))
    
    from ml.utils.data import load_sample_series  # type: ignore
    from ml.baselines.xgboost_ts import fit_xgb_and_forecast  # type: ignore
    
    series = load_sample_series(run.brand_id)
    forecast_df = fit_xgb_and_forecast(series, horizon=run.horizon)
    
    return [
        ForecastPoint(step=int(row.step), yhat=float(row.yhat))
        for row in forecast_df.itertuples(index=False)
    ]
