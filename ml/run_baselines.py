from __future__ import annotations

import os
import mlflow

from ml.utils.data import load_sample_series
from ml.baselines.arima import fit_arima_and_forecast
from ml.baselines.xgboost_ts import fit_xgb_and_forecast


def main():
	# Configure MLflow to local file store if not provided
	if not mlflow.get_tracking_uri():
		mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", f"file://{os.path.abspath('./mlruns')}"))
	series = load_sample_series("BRAND_A")
	with mlflow.start_run(run_name="baseline_comparison"):
		arima_df = fit_arima_and_forecast(series, horizon=12)
		xgb_df = fit_xgb_and_forecast(series, horizon=12)
		# Log artifacts for quick inspection
		arima_df.to_csv("arima_forecast.csv", index=False)
		mlflow.log_artifact("arima_forecast.csv")
		xgb_df.to_csv("xgb_forecast.csv", index=False)
		mlflow.log_artifact("xgb_forecast.csv")
	print("ARIMA and XGBoost forecasts saved as artifacts.")


if __name__ == "__main__":
	main()

