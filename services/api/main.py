from fastapi import FastAPI
from routers import baseline, runs, backtesting, scenarios, dashboard, auth, hierarchical, advanced_models, monitoring, streaming, data_upload


app = FastAPI(
    title="Pharma Forecasting API",
    version="2.0.0",
    description="Enterprise-grade pharmaceutical demand forecasting and analytics platform",
    docs_url="/docs",
    redoc_url="/redoc"
)


@app.get("/health")
def health():
	return {"status": "ok", "version": "2.0.0"}


# Public endpoints (no auth required)
app.include_router(auth.router)

# Protected endpoints (auth required)
app.include_router(baseline.router)
app.include_router(runs.router)
app.include_router(backtesting.router)
app.include_router(scenarios.router)
app.include_router(dashboard.router)
app.include_router(hierarchical.router)
app.include_router(advanced_models.router)
app.include_router(monitoring.router)
app.include_router(streaming.router)
app.include_router(data_upload.router)


if __name__ == "__main__":
	# Allows: python services/api/main.py (development only)
	import uvicorn
	uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

