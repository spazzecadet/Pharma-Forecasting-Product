# Pharma Forecasting Platform - Testing Guide

## 🚀 Quick Start Testing

### 1. Start the Backend API

```bash
# Navigate to the project root
cd /Users/gnanarammohankumar/pharma-forecasting

# Install Python dependencies
pip install -r services/api/requirements.txt
pip install -r ml/requirements.txt

# Start the API server
cd services/api
python main.py
```

The API will be available at: `http://localhost:8000`

### 2. Start the Frontend (Optional)

```bash
# In a new terminal, navigate to the UI directory
cd apps/ui

# Install dependencies (if Node.js is available)
npm install

# Start the development server
npm run dev
```

The frontend will be available at: `http://localhost:3000`

## 🔐 Authentication Testing

### Login to get JWT Token

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}'
```

**Expected Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user_id": "admin-001",
  "role": "admin"
}
```

**Save the token for subsequent requests:**
```bash
export TOKEN="your-jwt-token-here"
```

## 📊 API Endpoint Testing

### 1. Health Check
```bash
curl http://localhost:8000/health
```

### 2. Dashboard Data
```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/dashboard/portfolio
```

### 3. Create a Forecast Run
```bash
curl -X POST "http://localhost:8000/runs/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "brand_id": "BRAND_A",
    "model_type": "arima",
    "horizon": 12,
    "parameters": {"order": [1,1,1]}
  }'
```

### 4. Execute the Run
```bash
# Replace {run_id} with the actual run ID from the previous response
curl -X POST "http://localhost:8000/runs/{run_id}/execute" \
  -H "Authorization: Bearer $TOKEN"
```

### 5. Get Run Results
```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/runs/{run_id}/result
```

### 6. Test Advanced Models

**Prophet Model:**
```bash
curl -X POST "http://localhost:8000/models/prophet" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "brand_id": "BRAND_A",
    "horizon": 12,
    "seasonality_mode": "additive",
    "include_holidays": true
  }'
```

**LSTM Model:**
```bash
curl -X POST "http://localhost:8000/models/lstm" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "brand_id": "BRAND_A",
    "horizon": 12,
    "lookback": 12,
    "lstm_units": 50
  }'
```

### 7. Test Hierarchical Forecasting
```bash
curl -X POST "http://localhost:8000/hierarchical/forecast" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "brand_hierarchy": {
      "Total": ["Brand_A", "Brand_B"],
      "Brand_A": ["Brand_A_US", "Brand_A_CA"]
    },
    "method": "bottom_up",
    "horizon": 12
  }'
```

### 8. Test Data Upload
```bash
# Upload demand data
curl -X POST "http://localhost:8000/data/upload/demand" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@data/sample/fact_demand.csv" \
  -F "brand_id=BRAND_A"
```

### 9. Test Model Monitoring
```bash
# Log performance metrics
curl -X POST "http://localhost:8000/monitoring/performance/log" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "brand_id": "BRAND_A",
    "model_id": "arima_001",
    "metrics": {
      "mape": 5.2,
      "mae": 100.5,
      "rmse": 150.3
    }
  }'

# Check for drift
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/monitoring/drift/check/BRAND_A/arima_001
```

## 🌐 Frontend Testing

### 1. Access the Login Page
Navigate to: `http://localhost:3000/login`

**Login Credentials:**
- Username: `admin`
- Password: `password`

### 2. Dashboard Features
- View portfolio overview
- Check recent activity
- Navigate to data upload

### 3. Data Upload Testing
1. Go to `/upload` page
2. Select data type (demand, brand, geo, pricing)
3. Upload sample CSV files
4. Verify validation and processing

## 📁 Sample Data Files

### Demand Data Template
```csv
brand_id,geo_id,date,demand,units
BRAND_A,US,2023-01-01,1000,5000
BRAND_A,US,2023-01-08,1200,6000
BRAND_A,US,2023-01-15,1100,5500
BRAND_A,US,2023-01-22,1300,6500
BRAND_A,US,2023-01-29,1150,5750
```

### Brand Data Template
```csv
brand_id,brand_name,molecule,therapeutic_area,launch_date
BRAND_A,Brand A,Molecule A,Oncology,2020-01-01
BRAND_B,Brand B,Molecule B,Cardiology,2019-06-15
BRAND_C,Brand C,Molecule C,Neurology,2021-03-10
```

### Geography Data Template
```csv
geo_id,geo_name,region,country,market_size
US,United States,North America,USA,1000000
CA,Canada,North America,Canada,500000
UK,United Kingdom,Europe,UK,750000
DE,Germany,Europe,Germany,800000
```

### Pricing Data Template
```csv
brand_id,geo_id,date,price,promotion_type,discount_pct
BRAND_A,US,2023-01-01,100.00,none,0
BRAND_A,US,2023-01-15,90.00,promotion,10
BRAND_A,US,2023-02-01,100.00,none,0
BRAND_A,US,2023-02-15,85.00,promotion,15
```

## 🧪 Automated Testing

### Run Unit Tests
```bash
# From project root
python -m pytest tests/ -v
```

### Run API Tests
```bash
# Test all API endpoints
python -m pytest tests/test_api.py -v
```

### Run ML Model Tests
```bash
# Test ML models
python -m pytest tests/test_ml_models.py -v
```

## 🔍 Troubleshooting

### Common Issues

1. **API Connection Refused**
   - Ensure the API server is running on port 8000
   - Check if there are any port conflicts

2. **Authentication Errors**
   - Verify the JWT token is valid and not expired
   - Check if the token is properly included in headers

3. **File Upload Issues**
   - Ensure file format is CSV or Excel
   - Check file size limits
   - Verify required columns are present

4. **Frontend Not Loading**
   - Check if Node.js and npm are installed
   - Verify all dependencies are installed
   - Check for any console errors

### Debug Mode

Enable debug logging:
```bash
export DEBUG=1
python services/api/main.py
```

### Logs

Check API logs for detailed error information:
```bash
tail -f logs/api.log
```

## 📈 Performance Testing

### Load Testing with Apache Bench
```bash
# Test API performance
ab -n 1000 -c 10 -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/dashboard/portfolio
```

### Memory Usage
```bash
# Monitor memory usage
ps aux | grep python
```

## 🚀 Production Testing

### Docker Testing
```bash
# Build and run with Docker
docker-compose up -d

# Test endpoints
curl http://localhost:8000/health
```

### Kubernetes Testing
```bash
# Deploy to Kubernetes
kubectl apply -f infra/kubernetes/

# Check pods
kubectl get pods -n pharma-forecasting

# Test services
kubectl port-forward svc/pharma-forecasting-api 8000:8000
```

## 📋 Test Checklist

- [ ] API health check
- [ ] Authentication flow
- [ ] Dashboard data loading
- [ ] Forecast run creation and execution
- [ ] Advanced model testing (Prophet, LSTM)
- [ ] Hierarchical forecasting
- [ ] Data upload functionality
- [ ] Model monitoring
- [ ] Frontend login and navigation
- [ ] File upload validation
- [ ] Error handling
- [ ] Performance testing

## 🆘 Support

If you encounter issues:
1. Check the logs for error messages
2. Verify all dependencies are installed
3. Ensure all services are running
4. Check network connectivity
5. Review the API documentation at `/docs`

For additional help, refer to the main README.md or create an issue in the repository.
