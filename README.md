# Pharma Forecasting Monorepo (MVP)

This repository contains a minimal, cloud-agnostic MVP scaffold:

- apps/ui — Next.js app (to be added)
- services/api — FastAPI service with health and baseline forecast endpoints
- ml — ML baselines (to be added)
- infra — infra scaffolding and docker-compose

## Prerequisites

- Docker Desktop (recommended for running services locally)
- Or: Python 3.11+ if running API without Docker

## Run API (Docker)

```bash
docker compose up --build api
```

Visit `http://localhost:8000/health` and `http://localhost:8000/docs`.

## Run API (Local Python)

```bash
cd services/api
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### API Endpoints

Install ML requirements for full functionality:

```bash
cd /Users/gnanarammohankumar/pharma-forecasting
python3 -m venv .venv && source .venv/bin/activate
pip install -r ml/requirements.txt
```

#### Core Endpoints

**Health Check**
```bash
curl http://localhost:8000/health
```

**Baseline Forecasting**
```bash
curl -s http://localhost:8000/baseline/arima \
  -H 'Content-Type: application/json' \
  -d '{"brand_id":"BRAND_A","horizon":12}' | jq .
```

**Forecast Runs Management**
```bash
# Create a run
curl -s http://localhost:8000/runs/ \
  -H 'Content-Type: application/json' \
  -d '{"brand_id":"BRAND_A","model_type":"arima","horizon":12}' | jq .

# List runs
curl -s http://localhost:8000/runs/ | jq .

# Execute run (replace RUN_ID)
curl -s -X POST http://localhost:8000/runs/RUN_ID/execute | jq .
```

**Backtesting**
```bash
# Single model backtest
curl -s http://localhost:8000/backtest/ \
  -H 'Content-Type: application/json' \
  -d '{"brand_id":"BRAND_A","model_type":"arima","test_periods":12}' | jq .

# Compare models
curl -s -X POST "http://localhost:8000/backtest/compare?brand_id=BRAND_A&test_periods=12" | jq .
```

**Scenario Analysis**
```bash
# Price scenario
curl -s -X POST "http://localhost:8000/scenarios/quick-price-test?brand_id=BRAND_A&baseline_price=100&scenario_price=110&horizon=12" | jq .

# Custom scenario
curl -s http://localhost:8000/scenarios/ \
  -H 'Content-Type: application/json' \
  -d '{
    "brand_id":"BRAND_A",
    "model_type":"arima",
    "horizon":12,
    "variables":[{
      "name":"coverage",
      "baseline_value":0.8,
      "scenario_value":0.9,
      "impact_factor":0.5
    }],
    "description":"Coverage increase scenario"
  }' | jq .
```

**Dashboard & Analytics**
```bash
# Portfolio overview
curl -s http://localhost:8000/dashboard/portfolio | jq .

# Brand metrics
curl -s http://localhost:8000/dashboard/brands/BRAND_A/metrics | jq .

# Accuracy metrics
curl -s http://localhost:8000/dashboard/accuracy | jq .

# Model comparison
curl -s http://localhost:8000/dashboard/model-comparison?brand_id=BRAND_A | jq .

# Health check
curl -s http://localhost:8000/dashboard/health-check | jq .
```

## Features Implemented

✅ **Core API Services**
- FastAPI backend with health checks and Swagger docs
- Forecast runs management (create, execute, track)
- Backtesting with rolling windows and metrics (MAPE, WAPE, MAE, RMSE, bias)
- Scenario simulation for what-if analysis
- Dashboard API for executive metrics and portfolio overview

✅ **ML & Experimentation**
- ARIMA and XGBoost baseline models
- MLflow integration for experiment tracking
- Model comparison and performance metrics
- Rolling window backtesting with configurable parameters

✅ **Data Management**
- Semantic data model with entities (Brand, Geography, Channel, etc.)
- Connector stubs for IQVIA and database sources
- Sample data with multiple brands and geographies
- Data quality validation framework

✅ **DevOps & CI/CD**
- GitHub Actions for Python linting and testing
- Docker support for API and MLflow services
- Pre-commit hooks for code quality
- Comprehensive test suite

## Next Steps

- Add authentication and authorization (SSO, RBAC)
- Implement hierarchical forecasting and reconciliation
- Add more ML models (Prophet, LSTM, TFT)
- Build React/Next.js frontend dashboard
- Add real-time data connectors
- Implement model monitoring and drift detection
- Add Dagster pipelines for training/forecast runs

