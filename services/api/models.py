from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ModelType(str, Enum):
    ARIMA = "arima"
    XGBOOST = "xgboost"
    ENSEMBLE = "ensemble"


class ForecastRun(BaseModel):
    run_id: str = Field(..., description="Unique run identifier")
    brand_id: str = Field(..., description="Brand identifier")
    model_type: ModelType = Field(..., description="Model used for forecasting")
    horizon: int = Field(..., gt=0, le=104, description="Forecast horizon")
    status: RunStatus = Field(default=RunStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    mlflow_run_id: Optional[str] = None
    params: Dict = Field(default_factory=dict)
    metrics: Dict = Field(default_factory=dict)


class ForecastPoint(BaseModel):
    step: int
    yhat: float
    yhat_lower: Optional[float] = None
    yhat_upper: Optional[float] = None


class ForecastResult(BaseModel):
    run_id: str
    brand_id: str
    model_type: ModelType
    horizon: int
    points: List[ForecastPoint]
    metadata: Dict = Field(default_factory=dict)


class CreateRunRequest(BaseModel):
    brand_id: str = Field(..., description="Brand identifier")
    model_type: ModelType = Field(..., description="Model to use")
    horizon: int = Field(..., gt=0, le=104, description="Forecast horizon")
    params: Dict = Field(default_factory=dict, description="Model parameters")


class BacktestRequest(BaseModel):
    brand_id: str = Field(..., description="Brand identifier")
    model_type: ModelType = Field(..., description="Model to backtest")
    test_periods: int = Field(..., gt=0, le=52, description="Number of periods to test")
    window_size: int = Field(default=52, gt=4, description="Training window size")
    params: Dict = Field(default_factory=dict)


class BacktestMetrics(BaseModel):
    mape: float
    wape: float
    mae: float
    rmse: float
    bias: float


class BacktestResult(BaseModel):
    brand_id: str
    model_type: ModelType
    test_periods: int
    window_size: int
    metrics: BacktestMetrics
    run_id: str
