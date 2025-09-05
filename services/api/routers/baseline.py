from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List


router = APIRouter(prefix="/baseline", tags=["baseline"])


class BaselineRequest(BaseModel):
	brand_id: str = Field(...)
	horizon: int = Field(..., gt=0, le=104)


class ForecastPoint(BaseModel):
	step: int
	yhat: float


class BaselineResponse(BaseModel):
	brand_id: str
	horizon: int
	points: List[ForecastPoint]


@router.post("/arima", response_model=BaselineResponse)
def arima_forecast(req: BaselineRequest):
	# Lazy import ML modules and add repo root to sys.path so `ml` can be found
	import sys
	from pathlib import Path

	repo_root = Path(__file__).resolve().parents[3]
	if str(repo_root) not in sys.path:
		sys.path.append(str(repo_root))

	from ml.utils.data import load_sample_series  # type: ignore
	from ml.baselines.arima import fit_arima_and_forecast  # type: ignore

	series = load_sample_series(req.brand_id)
	forecast_df = fit_arima_and_forecast(series, horizon=req.horizon)
	points = [ForecastPoint(step=int(r.step), yhat=float(r.yhat)) for r in forecast_df.itertuples(index=False)]
	return BaselineResponse(brand_id=req.brand_id, horizon=req.horizon, points=points)

