from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
import sys
from pathlib import Path

from auth.dependencies import get_current_user, require_permission
from auth.models import User

router = APIRouter(prefix="/models", tags=["advanced_models"])

# Add repo root to path for ML imports
repo_root = Path(__file__).resolve().parents[3]
if str(repo_root) not in sys.path:
    sys.path.append(str(repo_root))

from ml.baselines.prophet_ts import fit_prophet_and_forecast, fit_prophet_with_holidays  # type: ignore
from ml.baselines.lstm_ts import fit_lstm_and_forecast, create_ensemble_lstm  # type: ignore
from ml.utils.data import load_sample_series  # type: ignore


class ProphetRequest(BaseModel):
    brand_id: str = Field(..., description="Brand identifier")
    horizon: int = Field(..., gt=0, le=104, description="Forecast horizon")
    seasonality_mode: str = Field(default="additive", description="Seasonality mode")
    yearly_seasonality: bool = Field(default=True, description="Include yearly seasonality")
    weekly_seasonality: bool = Field(default=True, description="Include weekly seasonality")
    daily_seasonality: bool = Field(default=False, description="Include daily seasonality")
    changepoint_prior_scale: float = Field(default=0.05, ge=0, le=1, description="Trend change flexibility")
    seasonality_prior_scale: float = Field(default=10.0, ge=0, le=100, description="Seasonality strength")
    include_holidays: bool = Field(default=False, description="Include pharma holidays")


class LSTMRequest(BaseModel):
    brand_id: str = Field(..., description="Brand identifier")
    horizon: int = Field(..., gt=0, le=104, description="Forecast horizon")
    lookback: int = Field(default=12, ge=4, le=52, description="Lookback period")
    lstm_units: int = Field(default=50, ge=10, le=200, description="LSTM units")
    epochs: int = Field(default=100, ge=10, le=500, description="Training epochs")
    batch_size: int = Field(default=32, ge=8, le=128, description="Batch size")
    dropout_rate: float = Field(default=0.2, ge=0, le=0.5, description="Dropout rate")
    learning_rate: float = Field(default=0.001, ge=0.0001, le=0.1, description="Learning rate")


class EnsembleLSTMRequest(BaseModel):
    brand_id: str = Field(..., description="Brand identifier")
    horizon: int = Field(..., gt=0, le=104, description="Forecast horizon")
    n_models: int = Field(default=3, ge=2, le=10, description="Number of models in ensemble")
    lookback: int = Field(default=12, ge=4, le=52, description="Lookback period")


class ForecastPoint(BaseModel):
    step: int
    yhat: float
    yhat_lower: Optional[float] = None
    yhat_upper: Optional[float] = None


class AdvancedForecastResponse(BaseModel):
    brand_id: str
    model_type: str
    horizon: int
    points: List[ForecastPoint]
    parameters: Dict = Field(default_factory=dict)


@router.post("/prophet", response_model=AdvancedForecastResponse)
def prophet_forecast(
    request: ProphetRequest,
    current_user: User = Depends(require_permission("models", "write"))
):
    """Generate Prophet forecast with configurable seasonality."""
    try:
        # Load data
        series = load_sample_series(request.brand_id)
        
        # Generate forecast
        if request.include_holidays:
            forecast_df = fit_prophet_with_holidays(series, request.horizon)
        else:
            forecast_df = fit_prophet_and_forecast(
                series=series,
                horizon=request.horizon,
                seasonality_mode=request.seasonality_mode,
                yearly_seasonality=request.yearly_seasonality,
                weekly_seasonality=request.weekly_seasonality,
                daily_seasonality=request.daily_seasonality,
                changepoint_prior_scale=request.changepoint_prior_scale,
                seasonality_prior_scale=request.seasonality_prior_scale
            )
        
        # Convert to response format
        points = []
        for _, row in forecast_df.iterrows():
            points.append(ForecastPoint(
                step=int(row['step']),
                yhat=float(row['yhat']),
                yhat_lower=float(row.get('yhat_lower', 0)) if 'yhat_lower' in row else None,
                yhat_upper=float(row.get('yhat_upper', 0)) if 'yhat_upper' in row else None
            ))
        
        return AdvancedForecastResponse(
            brand_id=request.brand_id,
            model_type="Prophet",
            horizon=request.horizon,
            points=points,
            parameters={
                "seasonality_mode": request.seasonality_mode,
                "yearly_seasonality": request.yearly_seasonality,
                "weekly_seasonality": request.weekly_seasonality,
                "daily_seasonality": request.daily_seasonality,
                "changepoint_prior_scale": request.changepoint_prior_scale,
                "seasonality_prior_scale": request.seasonality_prior_scale,
                "include_holidays": request.include_holidays
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prophet forecasting failed: {str(e)}")


@router.post("/lstm", response_model=AdvancedForecastResponse)
def lstm_forecast(
    request: LSTMRequest,
    current_user: User = Depends(require_permission("models", "write"))
):
    """Generate LSTM forecast with configurable architecture."""
    try:
        # Load data
        series = load_sample_series(request.brand_id)
        
        # Generate forecast
        forecast_df = fit_lstm_and_forecast(
            series=series,
            horizon=request.horizon,
            lookback=request.lookback,
            lstm_units=request.lstm_units,
            epochs=request.epochs,
            batch_size=request.batch_size,
            dropout_rate=request.dropout_rate,
            learning_rate=request.learning_rate
        )
        
        # Convert to response format
        points = []
        for _, row in forecast_df.iterrows():
            points.append(ForecastPoint(
                step=int(row['step']),
                yhat=float(row['yhat'])
            ))
        
        return AdvancedForecastResponse(
            brand_id=request.brand_id,
            model_type="LSTM",
            horizon=request.horizon,
            points=points,
            parameters={
                "lookback": request.lookback,
                "lstm_units": request.lstm_units,
                "epochs": request.epochs,
                "batch_size": request.batch_size,
                "dropout_rate": request.dropout_rate,
                "learning_rate": request.learning_rate
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LSTM forecasting failed: {str(e)}")


@router.post("/ensemble-lstm", response_model=AdvancedForecastResponse)
def ensemble_lstm_forecast(
    request: EnsembleLSTMRequest,
    current_user: User = Depends(require_permission("models", "write"))
):
    """Generate ensemble LSTM forecast for robust predictions."""
    try:
        # Load data
        series = load_sample_series(request.brand_id)
        
        # Generate ensemble forecast
        forecast_df = create_ensemble_lstm(
            series=series,
            horizon=request.horizon,
            n_models=request.n_models,
            lookback=request.lookback
        )
        
        # Convert to response format
        points = []
        for _, row in forecast_df.iterrows():
            points.append(ForecastPoint(
                step=int(row['step']),
                yhat=float(row['yhat']),
                yhat_lower=float(row.get('yhat_lower', 0)) if 'yhat_lower' in row else None,
                yhat_upper=float(row.get('yhat_upper', 0)) if 'yhat_upper' in row else None
            ))
        
        return AdvancedForecastResponse(
            brand_id=request.brand_id,
            model_type="Ensemble_LSTM",
            horizon=request.horizon,
            points=points,
            parameters={
                "n_models": request.n_models,
                "lookback": request.lookback
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ensemble LSTM forecasting failed: {str(e)}")


@router.get("/available")
def get_available_models(current_user: User = Depends(require_permission("models", "read"))):
    """Get list of available advanced models."""
    return {
        "models": [
            {
                "name": "Prophet",
                "description": "Facebook's Prophet for time series with seasonality",
                "strengths": ["Handles seasonality well", "Robust to missing data", "Interpretable"],
                "use_cases": ["Seasonal patterns", "Holiday effects", "Trend analysis"],
                "parameters": [
                    "seasonality_mode", "yearly_seasonality", "weekly_seasonality",
                    "changepoint_prior_scale", "seasonality_prior_scale"
                ]
            },
            {
                "name": "LSTM",
                "description": "Long Short-Term Memory neural network",
                "strengths": ["Captures complex patterns", "Non-linear relationships", "Sequence learning"],
                "use_cases": ["Complex patterns", "Non-linear trends", "Sequence dependencies"],
                "parameters": [
                    "lookback", "lstm_units", "epochs", "batch_size",
                    "dropout_rate", "learning_rate"
                ]
            },
            {
                "name": "Ensemble_LSTM",
                "description": "Ensemble of multiple LSTM models",
                "strengths": ["Robust predictions", "Uncertainty quantification", "Reduced overfitting"],
                "use_cases": ["High-stakes decisions", "Uncertainty analysis", "Robust forecasting"],
                "parameters": ["n_models", "lookback"]
            }
        ]
    }
