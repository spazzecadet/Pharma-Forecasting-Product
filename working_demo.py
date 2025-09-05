#!/usr/bin/env python3
"""
WORKING PHARMA FORECASTING DEMO
This is a simplified, working version you can actually run and test.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import json
import random
from datetime import datetime, timedelta

app = FastAPI(
    title="Pharma Forecasting API - WORKING DEMO",
    version="1.0.0",
    description="Simplified working version of the pharma forecasting platform"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data Models
class LoginRequest(BaseModel):
    username: str
    password: str

class ForecastRequest(BaseModel):
    brand_id: str
    horizon: int = 12
    model_type: str = "arima"

class ForecastPoint(BaseModel):
    step: int
    yhat: float
    yhat_lower: float = None
    yhat_upper: float = None

class ForecastResponse(BaseModel):
    brand_id: str
    model_type: str
    horizon: int
    points: List[ForecastPoint]
    created_at: str

# Mock Data
MOCK_BRANDS = ["BRAND_A", "BRAND_B", "BRAND_C"]
MOCK_USERS = {
    "admin": {"password": "password", "role": "admin"},
    "analyst": {"password": "analyst123", "role": "analyst"}
}

# API Endpoints
@app.get("/")
def root():
    return {
        "message": "🎉 Pharma Forecasting API - WORKING DEMO",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "login": "/auth/login",
            "forecast": "/forecast",
            "dashboard": "/dashboard",
            "docs": "/docs"
        }
    }

@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.post("/auth/login")
def login(request: LoginRequest):
    """Simple login - returns mock token"""
    if request.username in MOCK_USERS and MOCK_USERS[request.username]["password"] == request.password:
        return {
            "access_token": f"mock_token_{request.username}_{datetime.now().timestamp()}",
            "token_type": "bearer",
            "user_id": request.username,
            "role": MOCK_USERS[request.username]["role"]
        }
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/forecast", response_model=ForecastResponse)
def create_forecast(request: ForecastRequest):
    """Generate mock forecast data"""
    if request.brand_id not in MOCK_BRANDS:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    # Generate mock forecast points
    base_value = random.uniform(1000, 2000)
    points = []
    
    for i in range(request.horizon):
        trend = i * random.uniform(10, 50)
        seasonality = 100 * random.uniform(-0.3, 0.3)
        noise = random.uniform(-50, 50)
        
        yhat = base_value + trend + seasonality + noise
        yhat_lower = yhat * random.uniform(0.85, 0.95)
        yhat_upper = yhat * random.uniform(1.05, 1.15)
        
        points.append(ForecastPoint(
            step=i + 1,
            yhat=round(yhat, 2),
            yhat_lower=round(yhat_lower, 2),
            yhat_upper=round(yhat_upper, 2)
        ))
    
    return ForecastResponse(
        brand_id=request.brand_id,
        model_type=request.model_type,
        horizon=request.horizon,
        points=points,
        created_at=datetime.now().isoformat()
    )

@app.get("/dashboard")
def get_dashboard():
    """Get mock dashboard data"""
    return {
        "total_brands": len(MOCK_BRANDS),
        "total_runs": random.randint(50, 200),
        "successful_runs": random.randint(45, 180),
        "avg_accuracy": round(random.uniform(85, 95), 1),
        "top_performing_brand": random.choice(MOCK_BRANDS),
        "recent_activity": [
            {
                "run_id": f"run_{i}",
                "brand": random.choice(MOCK_BRANDS),
                "model": random.choice(["arima", "xgboost", "prophet"]),
                "status": random.choice(["completed", "running", "failed"]),
                "date": (datetime.now() - timedelta(hours=i)).isoformat()
            }
            for i in range(5)
        ]
    }

@app.get("/brands")
def get_brands():
    """Get available brands"""
    return {"brands": MOCK_BRANDS}

@app.get("/models")
def get_models():
    """Get available models"""
    return {
        "models": [
            {"name": "arima", "description": "ARIMA time series model"},
            {"name": "xgboost", "description": "XGBoost gradient boosting"},
            {"name": "prophet", "description": "Facebook Prophet"},
            {"name": "lstm", "description": "LSTM neural network"}
        ]
    }

@app.post("/upload/demand")
def upload_demand_data(brand_id: str, file_data: str = "mock_csv_data"):
    """Mock file upload"""
    return {
        "success": True,
        "message": f"Successfully uploaded demand data for {brand_id}",
        "records_processed": random.randint(100, 1000)
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Pharma Forecasting API - WORKING DEMO")
    print("📊 Available at: http://localhost:8000")
    print("📚 API Docs at: http://localhost:8000/docs")
    print("🔑 Login: admin/password or analyst/analyst123")
    uvicorn.run(app, host="0.0.0.0", port=8000)
