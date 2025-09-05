from __future__ import annotations

from typing import List

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error
from xgboost import XGBRegressor
import mlflow


def _make_lag_features(values: np.ndarray, lags: List[int]) -> np.ndarray:
	max_lag = max(lags)
	rows = []
	for t in range(max_lag, len(values)):
		row = [values[t - lag] for lag in lags]
		rows.append(row)
	return np.asarray(rows)


def fit_xgb_and_forecast(series: pd.Series, horizon: int, lags: List[int] | None = None) -> pd.DataFrame:
	"""Train XGBRegressor on lag features and forecast via recursive strategy."""
	if lags is None:
		lags = [1, 2, 3, 4, 6, 12]
	values = series.astype(float).to_numpy()
	X = _make_lag_features(values, lags)
	y = values[max(lags) :]
	with mlflow.start_run(nested=True):
		mlflow.log_params({"model": "XGBRegressor", "lags": ",".join(map(str, lags)), "horizon": horizon})
		model = XGBRegressor(
			n_estimators=300,
			max_depth=4,
			learning_rate=0.05,
			subsample=0.9,
			colsample_bytree=0.9,
			random_state=42,
		)
		model.fit(X, y)
		# In-sample MAE for sanity
		mae = mean_absolute_error(y, model.predict(X))
		mlflow.log_metric("train_mae", float(mae))
		# Recursive forecast
		history = values.tolist()
		preds = []
		for step in range(horizon):
			feat = np.asarray([[history[-lag] for lag in lags]])
			yhat = float(model.predict(feat)[0])
			preds.append(yhat)
			history.append(yhat)
		return pd.DataFrame({"step": np.arange(1, horizon + 1), "yhat": preds})

