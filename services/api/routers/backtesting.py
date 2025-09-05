from fastapi import APIRouter, HTTPException
from models import BacktestRequest, BacktestResult, BacktestMetrics, ModelType

router = APIRouter(prefix="/backtest", tags=["backtesting"])


@router.post("/", response_model=BacktestResult)
def run_backtest(req: BacktestRequest):
    """Run backtesting for a specific model and brand."""
    import sys
    from pathlib import Path
    import uuid
    
    # Add repo root to path for imports
    repo_root = Path(__file__).resolve().parents[3]
    if str(repo_root) not in sys.path:
        sys.path.append(str(repo_root))
    
    try:
        from ml.evaluation.backtesting import backtest_model  # type: ignore
        from ml.baselines.arima import fit_arima_and_forecast  # type: ignore
        from ml.baselines.xgboost_ts import fit_xgb_and_forecast  # type: ignore
        
        # Select forecast function based on model type
        if req.model_type == ModelType.ARIMA:
            forecast_func = lambda series, horizon: fit_arima_and_forecast(series, horizon)
        elif req.model_type == ModelType.XGBOOST:
            forecast_func = lambda series, horizon: fit_xgb_and_forecast(series, horizon)
        else:
            raise HTTPException(status_code=400, detail="Unsupported model type")
        
        # Run backtest
        metrics_dict = backtest_model(
            brand_id=req.brand_id,
            model_name=req.model_type.value,
            forecast_func=forecast_func,
            test_periods=req.test_periods,
            window_size=req.window_size,
        )
        
        # Convert to response model
        metrics = BacktestMetrics(
            mape=metrics_dict['mape'],
            wape=metrics_dict['wape'],
            mae=metrics_dict['mae'],
            rmse=metrics_dict['rmse'],
            bias=metrics_dict['bias']
        )
        
        run_id = str(uuid.uuid4())
        
        return BacktestResult(
            brand_id=req.brand_id,
            model_type=req.model_type,
            test_periods=req.test_periods,
            window_size=req.window_size,
            metrics=metrics,
            run_id=run_id
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backtesting failed: {str(e)}")


@router.post("/compare")
def compare_models(brand_id: str, test_periods: int = 12, window_size: int = 52):
    """Compare ARIMA vs XGBoost performance via backtesting."""
    import sys
    from pathlib import Path
    
    repo_root = Path(__file__).resolve().parents[3]
    if str(repo_root) not in sys.path:
        sys.path.append(str(repo_root))
    
    try:
        from ml.evaluation.backtesting import backtest_model  # type: ignore
        from ml.baselines.arima import fit_arima_and_forecast  # type: ignore
        from ml.baselines.xgboost_ts import fit_xgb_and_forecast  # type: ignore
        
        results = {}
        
        # Test ARIMA
        arima_metrics = backtest_model(
            brand_id=brand_id,
            model_name="arima",
            forecast_func=lambda series, horizon: fit_arima_and_forecast(series, horizon),
            test_periods=test_periods,
            window_size=window_size,
        )
        results['arima'] = arima_metrics
        
        # Test XGBoost
        xgb_metrics = backtest_model(
            brand_id=brand_id,
            model_name="xgboost",
            forecast_func=lambda series, horizon: fit_xgb_and_forecast(series, horizon),
            test_periods=test_periods,
            window_size=window_size,
        )
        results['xgboost'] = xgb_metrics
        
        # Determine winner based on MAPE
        winner = "arima" if arima_metrics['mape'] < xgb_metrics['mape'] else "xgboost"
        
        return {
            "brand_id": brand_id,
            "test_periods": test_periods,
            "window_size": window_size,
            "results": results,
            "winner": winner,
            "winner_mape": results[winner]['mape']
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model comparison failed: {str(e)}")
