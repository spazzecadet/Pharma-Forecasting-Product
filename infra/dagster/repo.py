from dagster import Definitions, job, op
import os
import mlflow
from ml.utils.data import load_sample_series
from ml.baselines.arima import fit_arima_and_forecast


@op
def run_arima_op():
	if not mlflow.get_tracking_uri():
		mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", f"file://{os.path.abspath('./mlruns')}"))
	series = load_sample_series("BRAND_A")
	fit_arima_and_forecast(series, horizon=12)


@job
def baseline_job():
	run_arima_op()


defs = Definitions(jobs=[baseline_job])

