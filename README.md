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

### Calling ARIMA endpoint

The ARIMA endpoint depends on ML libraries. Install ML requirements first:

```bash
cd /Users/gnanarammohankumar/pharma-forecasting
python3 -m venv .venv && source .venv/bin/activate
pip install -r ml/requirements.txt
```

Then, with the API running, POST:

```bash
curl -s http://localhost:8000/baseline/arima \
  -H 'Content-Type: application/json' \
  -d '{"brand_id":"BRAND_A","horizon":12}' | jq .
```

## Next Steps

- Add ML baselines (ARIMA + XGBoost) with MLflow tracking
- Scaffold Next.js UI
- Add Dagster pipelines for training/forecast runs

