# Pharma Forecasting API Documentation

## Overview

The Pharma Forecasting API is a comprehensive, enterprise-grade platform for pharmaceutical demand forecasting and analytics. It provides RESTful endpoints for forecasting, model management, scenario analysis, and real-time monitoring.

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://pharma-forecasting.yourdomain.com/api`

## Authentication

The API uses JWT (JSON Web Tokens) for authentication. Include the token in the Authorization header:

```bash
Authorization: Bearer <your-jwt-token>
```

### Getting Started

1. **Login** to get an access token:
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}'
```

2. **Use the token** in subsequent requests:
```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/dashboard/portfolio"
```

## API Endpoints

### Authentication & Users

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/auth/login` | Login and get JWT token | No |
| GET | `/auth/me` | Get current user info | Yes |
| POST | `/auth/users` | Create new user | Admin |
| GET | `/auth/users` | List all users | Admin |

### Forecasting

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/runs/` | Create forecast run | Yes |
| GET | `/runs/` | List forecast runs | Yes |
| GET | `/runs/{run_id}` | Get specific run | Yes |
| POST | `/runs/{run_id}/execute` | Execute forecast run | Yes |
| GET | `/runs/{run_id}/result` | Get run results | Yes |

### Models

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/models/prophet` | Prophet forecasting | Yes |
| POST | `/models/lstm` | LSTM forecasting | Yes |
| POST | `/models/ensemble-lstm` | Ensemble LSTM | Yes |
| GET | `/models/available` | List available models | Yes |

### Backtesting

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/backtest/` | Run backtest | Yes |
| POST | `/backtest/compare` | Compare models | Yes |

### Scenarios

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/scenarios/` | Create scenario | Yes |
| GET | `/scenarios/` | List scenarios | Yes |
| GET | `/scenarios/{scenario_id}` | Get scenario | Yes |
| POST | `/scenarios/quick-price-test` | Quick price test | Yes |

### Hierarchical Forecasting

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/hierarchical/forecast` | Hierarchical forecast | Yes |
| GET | `/hierarchical/pharma-hierarchy` | Get hierarchy | Yes |
| POST | `/hierarchical/reconcile` | Reconcile forecasts | Yes |
| GET | `/hierarchical/methods` | List methods | Yes |

### Monitoring

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/monitoring/performance/log` | Log performance | Yes |
| GET | `/monitoring/drift/check/{brand_id}/{model_id}` | Check drift | Yes |
| GET | `/monitoring/alerts` | Get alerts | Yes |
| GET | `/monitoring/performance/trend/{brand_id}/{model_id}/{metric}` | Performance trend | Yes |

### Dashboard

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/dashboard/portfolio` | Portfolio overview | Yes |
| GET | `/dashboard/brands/{brand_id}/metrics` | Brand metrics | Yes |
| GET | `/dashboard/accuracy` | Accuracy metrics | Yes |
| GET | `/dashboard/model-comparison` | Model comparison | Yes |

### Streaming

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| WebSocket | `/streaming/ws` | Real-time data stream | Optional |
| GET | `/streaming/sources` | List data sources | Optional |
| GET | `/streaming/sources/{source_name}/data` | Get source data | Optional |

## Response Formats

### Success Response
```json
{
  "data": { ... },
  "message": "Success",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### Error Response
```json
{
  "error": "Error message",
  "detail": "Detailed error information",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Rate Limiting

- **Standard endpoints**: 100 requests per minute
- **Heavy operations** (forecasting, backtesting): 10 requests per minute
- **Streaming**: No limit

## Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 422 | Validation Error |
| 429 | Rate Limited |
| 500 | Internal Server Error |

## SDKs and Examples

### Python SDK
```python
from pharma_forecasting import PharmaForecastingClient

client = PharmaForecastingClient(
    base_url="http://localhost:8000",
    api_key="your-jwt-token"
)

# Create a forecast run
run = client.runs.create(
    brand_id="BRAND_A",
    model_type="arima",
    horizon=12
)

# Execute the run
result = client.runs.execute(run.id)
```

### JavaScript SDK
```javascript
import { PharmaForecastingClient } from '@pharma/forecasting-sdk';

const client = new PharmaForecastingClient({
  baseUrl: 'http://localhost:8000',
  apiKey: 'your-jwt-token'
});

// Create a forecast run
const run = await client.runs.create({
  brand_id: 'BRAND_A',
  model_type: 'arima',
  horizon: 12
});

// Execute the run
const result = await client.runs.execute(run.id);
```

## Webhooks

The API supports webhooks for real-time notifications:

- **Forecast completed**: When a forecast run finishes
- **Drift detected**: When model drift is detected
- **Performance degraded**: When model performance drops

### Webhook Configuration
```json
{
  "url": "https://your-app.com/webhooks/forecast-completed",
  "events": ["forecast.completed", "drift.detected"],
  "secret": "your-webhook-secret"
}
```

## Support

For API support and questions:
- **Documentation**: [https://docs.pharma-forecasting.com](https://docs.pharma-forecasting.com)
- **Support Email**: support@pharma-forecasting.com
- **Status Page**: [https://status.pharma-forecasting.com](https://status.pharma-forecasting.com)
