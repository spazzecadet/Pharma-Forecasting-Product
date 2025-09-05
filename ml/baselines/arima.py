from __future__ import annotations

import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
import mlflow


def fit_arima_and_forecast(series: pd.Series, horizon: int, order=(1, 1, 1)) -> pd.DataFrame:
	"""Fit ARIMA on a pandas Series and forecast horizon steps ahead.

	Returns a DataFrame with columns: step, yhat
	"""
	series = series.astype(float)
	with mlflow.start_run(nested=True):
		mlflow.log_params({"model": "ARIMA", "p": order[0], "d": order[1], "q": order[2], "horizon": horizon})
		model = ARIMA(series, order=order)
		res = model.fit()
		forecast = res.forecast(steps=horizon)
		pred = forecast.reset_index(drop=True).rename("yhat")
		pred.index = pred.index + 1
		out = pred.reset_index().rename(columns={"index": "step"})
		mlflow.log_metric("aic", float(getattr(res, "aic", float("nan"))))
		return out

