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

## Next Steps

- Add ML baselines (ARIMA + XGBoost) with MLflow tracking
- Scaffold Next.js UI
- Add Dagster pipelines for training/forecast runs

