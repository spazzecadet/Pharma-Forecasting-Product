#!/usr/bin/env python3
"""
PHARMA FORECASTING PLATFORM - FULL WEB APPLICATION
Beautiful UI with modern design and intuitive UX
"""

import sys
import os
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import json
import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import io
import uvicorn

# Create FastAPI app
app = FastAPI(
    title="Pharma Forecasting Platform",
    version="2.0.0",
    description="Enterprise-grade pharmaceutical demand forecasting and analytics platform"
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
    horizon: int = Field(default=12, ge=1, le=52)
    model_type: str = Field(default="arima")

class ForecastPoint(BaseModel):
    step: int
    yhat: float
    yhat_lower: Optional[float] = None
    yhat_upper: Optional[float] = None

class ForecastResponse(BaseModel):
    brand_id: str
    model_type: str
    horizon: int
    points: List[ForecastPoint]
    created_at: str
    accuracy: float

# Mock Data Storage
MOCK_BRANDS = [
    {"id": "BRAND_A", "name": "OncoMed A", "molecule": "Molecule A", "therapeutic_area": "Oncology", "revenue": 125000000},
    {"id": "BRAND_B", "name": "CardioMax B", "molecule": "Molecule B", "therapeutic_area": "Cardiology", "revenue": 89000000},
    {"id": "BRAND_C", "name": "NeuroFlex C", "molecule": "Molecule C", "therapeutic_area": "Neurology", "revenue": 156000000},
    {"id": "BRAND_D", "name": "ImmuneGuard D", "molecule": "Molecule D", "therapeutic_area": "Immunology", "revenue": 203000000}
]

MOCK_GEOS = ["US", "CA", "UK", "DE", "FR", "JP"]
MOCK_USERS = {
    "admin": {"password": "password", "role": "admin", "brands": [b["id"] for b in MOCK_BRANDS]},
    "analyst": {"password": "analyst123", "role": "analyst", "brands": ["BRAND_A", "BRAND_B"]},
    "viewer": {"password": "viewer123", "role": "viewer", "brands": ["BRAND_A"]}
}

# In-memory storage
forecast_runs = []
upload_history = []

# Utility Functions
def generate_mock_forecast(brand_id: str, horizon: int, model_type: str) -> List[ForecastPoint]:
    """Generate realistic mock forecast data"""
    base_value = random.uniform(1000, 2000)
    points = []
    
    for i in range(horizon):
        # Add trend
        trend = i * random.uniform(5, 25)
        
        # Add seasonality (weekly pattern)
        seasonality = 50 * np.sin(2 * np.pi * i / 7) + 25 * np.sin(2 * np.pi * i / 30)
        
        # Add noise
        noise = random.uniform(-30, 30)
        
        yhat = base_value + trend + seasonality + noise
        
        # Generate confidence intervals
        yhat_lower = yhat * random.uniform(0.85, 0.95)
        yhat_upper = yhat * random.uniform(1.05, 1.15)
        
        points.append(ForecastPoint(
            step=i + 1,
            yhat=round(yhat, 2),
            yhat_lower=round(yhat_lower, 2),
            yhat_upper=round(yhat_upper, 2)
        ))
    
    return points

def calculate_accuracy(points: List[ForecastPoint]) -> float:
    """Calculate mock accuracy based on forecast variance"""
    if not points:
        return 0.0
    
    values = [p.yhat for p in points]
    variance = np.var(values)
    # Lower variance = higher accuracy
    accuracy = max(70, min(95, 90 - (variance / 100)))
    return round(accuracy, 1)

# HTML Templates
def get_main_page():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pharma Forecasting Platform</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js" defer></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .gradient-bg { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .card-hover { transition: all 0.3s ease; }
        .card-hover:hover { transform: translateY(-5px); box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1); }
        .chart-container { position: relative; height: 400px; }
        .loading { animation: spin 1s linear infinite; }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
    </style>
</head>
<body class="bg-gray-50" x-data="pharmaApp()">
    <!-- Navigation -->
    <nav class="gradient-bg shadow-lg">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-16">
                <div class="flex items-center">
                    <i class="fas fa-chart-line text-white text-2xl mr-3"></i>
                    <h1 class="text-white text-xl font-bold">Pharma Forecasting Platform</h1>
                </div>
                <div class="flex items-center space-x-4">
                    <span class="text-white" x-text="user?.username || 'Guest'"></span>
                    <button @click="logout()" class="text-white hover:text-gray-200" x-show="user">
                        <i class="fas fa-sign-out-alt"></i>
                    </button>
                </div>
            </div>
        </div>
    </nav>

    <!-- Login Modal -->
    <div x-show="!user" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
        <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div class="mt-3">
                <h3 class="text-lg font-medium text-gray-900 text-center mb-4">Login to Platform</h3>
                <form @submit.prevent="login()">
                    <div class="mb-4">
                        <label class="block text-gray-700 text-sm font-bold mb-2">Username</label>
                        <input x-model="loginForm.username" type="text" class="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" required>
                    </div>
                    <div class="mb-6">
                        <label class="block text-gray-700 text-sm font-bold mb-2">Password</label>
                        <input x-model="loginForm.password" type="password" class="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" required>
                    </div>
                    <div class="flex justify-center">
                        <button type="submit" class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline">
                            Login
                        </button>
                    </div>
                </form>
                <div class="mt-4 text-sm text-gray-600">
                    <p>Demo accounts:</p>
                    <p>• admin / password</p>
                    <p>• analyst / analyst123</p>
                    <p>• viewer / viewer123</p>
                </div>
            </div>
        </div>
    </div>

    <!-- Main Content -->
    <div x-show="user" class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <!-- Dashboard Header -->
        <div class="mb-8">
            <h2 class="text-3xl font-bold text-gray-900">Dashboard</h2>
            <p class="mt-2 text-gray-600">Pharmaceutical demand forecasting and analytics</p>
        </div>

        <!-- Stats Cards -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div class="bg-white overflow-hidden shadow rounded-lg card-hover">
                <div class="p-5">
                    <div class="flex items-center">
                        <div class="flex-shrink-0">
                            <i class="fas fa-pills text-blue-500 text-2xl"></i>
                        </div>
                        <div class="ml-5 w-0 flex-1">
                            <dl>
                                <dt class="text-sm font-medium text-gray-500 truncate">Total Brands</dt>
                                <dd class="text-lg font-medium text-gray-900" x-text="stats.total_brands"></dd>
                            </dl>
                        </div>
                    </div>
                </div>
            </div>

            <div class="bg-white overflow-hidden shadow rounded-lg card-hover">
                <div class="p-5">
                    <div class="flex items-center">
                        <div class="flex-shrink-0">
                            <i class="fas fa-chart-bar text-green-500 text-2xl"></i>
                        </div>
                        <div class="ml-5 w-0 flex-1">
                            <dl>
                                <dt class="text-sm font-medium text-gray-500 truncate">Forecast Runs</dt>
                                <dd class="text-lg font-medium text-gray-900" x-text="stats.total_runs"></dd>
                            </dl>
                        </div>
                    </div>
                </div>
            </div>

            <div class="bg-white overflow-hidden shadow rounded-lg card-hover">
                <div class="p-5">
                    <div class="flex items-center">
                        <div class="flex-shrink-0">
                            <i class="fas fa-percentage text-yellow-500 text-2xl"></i>
                        </div>
                        <div class="ml-5 w-0 flex-1">
                            <dl>
                                <dt class="text-sm font-medium text-gray-500 truncate">Avg Accuracy</dt>
                                <dd class="text-lg font-medium text-gray-900" x-text="stats.avg_accuracy + '%'"></dd>
                            </dl>
                        </div>
                    </div>
                </div>
            </div>

            <div class="bg-white overflow-hidden shadow rounded-lg card-hover">
                <div class="p-5">
                    <div class="flex items-center">
                        <div class="flex-shrink-0">
                            <i class="fas fa-trophy text-purple-500 text-2xl"></i>
                        </div>
                        <div class="ml-5 w-0 flex-1">
                            <dl>
                                <dt class="text-sm font-medium text-gray-500 truncate">Top Brand</dt>
                                <dd class="text-lg font-medium text-gray-900" x-text="stats.top_performing_brand"></dd>
                            </dl>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Main Content Grid -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <!-- Forecast Creation -->
            <div class="bg-white shadow rounded-lg p-6">
                <h3 class="text-lg font-medium text-gray-900 mb-4">
                    <i class="fas fa-magic mr-2"></i>Create New Forecast
                </h3>
                <form @submit.prevent="createForecast()">
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">Brand</label>
                            <select x-model="forecastForm.brand_id" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" required>
                                <option value="">Select Brand</option>
                                <template x-for="brand in brands" :key="brand.id">
                                    <option :value="brand.id" x-text="brand.name"></option>
                                </template>
                            </select>
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">Model</label>
                            <select x-model="forecastForm.model_type" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" required>
                                <option value="arima">ARIMA</option>
                                <option value="xgboost">XGBoost</option>
                                <option value="prophet">Prophet</option>
                                <option value="lstm">LSTM</option>
                            </select>
                        </div>
                    </div>
                    <div class="mb-4">
                        <label class="block text-sm font-medium text-gray-700 mb-2">Forecast Horizon (weeks)</label>
                        <input x-model="forecastForm.horizon" type="number" min="1" max="52" value="12" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" required>
                    </div>
                    <button type="submit" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline">
                        <i class="fas fa-play mr-2"></i>Generate Forecast
                    </button>
                </form>
            </div>

            <!-- Recent Activity -->
            <div class="bg-white shadow rounded-lg p-6">
                <h3 class="text-lg font-medium text-gray-900 mb-4">
                    <i class="fas fa-history mr-2"></i>Recent Activity
                </h3>
                <div class="space-y-3">
                    <template x-for="activity in recentActivity" :key="activity.run_id">
                        <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                            <div>
                                <p class="text-sm font-medium text-gray-900" x-text="activity.brand_id"></p>
                                <p class="text-xs text-gray-500" x-text="activity.model_type + ' • ' + activity.horizon + ' weeks'"></p>
                            </div>
                            <div class="text-right">
                                <p class="text-sm font-medium text-green-600" x-text="activity.accuracy + '%'"></p>
                                <p class="text-xs text-gray-500" x-text="new Date(activity.created_at).toLocaleDateString()"></p>
                            </div>
                        </div>
                    </template>
                </div>
            </div>
        </div>

        <!-- Forecast Chart -->
        <div x-show="currentForecast" class="mt-8 bg-white shadow rounded-lg p-6">
            <h3 class="text-lg font-medium text-gray-900 mb-4">
                <i class="fas fa-chart-line mr-2"></i>Forecast Visualization
            </h3>
            <div class="chart-container">
                <canvas id="forecastChart"></canvas>
            </div>
        </div>

        <!-- File Upload -->
        <div class="mt-8 bg-white shadow rounded-lg p-6">
            <h3 class="text-lg font-medium text-gray-900 mb-4">
                <i class="fas fa-upload mr-2"></i>Upload Data Files
            </h3>
            <div class="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                <input type="file" @change="handleFileUpload($event)" accept=".csv,.xlsx,.xls" class="hidden" id="fileInput">
                <label for="fileInput" class="cursor-pointer">
                    <i class="fas fa-cloud-upload-alt text-4xl text-gray-400 mb-4"></i>
                    <p class="text-lg text-gray-600">Click to upload or drag and drop</p>
                    <p class="text-sm text-gray-500">CSV, XLSX files up to 10MB</p>
                </label>
            </div>
            <div x-show="uploadStatus" class="mt-4 p-4 bg-green-50 border border-green-200 rounded-md">
                <p class="text-green-800" x-text="uploadStatus"></p>
            </div>
        </div>
    </div>

    <script>
        function pharmaApp() {
            return {
                user: null,
                brands: [],
                stats: {
                    total_brands: 0,
                    total_runs: 0,
                    avg_accuracy: 0,
                    top_performing_brand: ''
                },
                recentActivity: [],
                currentForecast: null,
                forecastForm: {
                    brand_id: '',
                    model_type: 'arima',
                    horizon: 12
                },
                loginForm: {
                    username: '',
                    password: ''
                },
                uploadStatus: '',

                async init() {
                    await this.loadBrands();
                    await this.loadStats();
                    await this.loadRecentActivity();
                },

                async loadBrands() {
                    try {
                        const response = await fetch('/api/brands');
                        this.brands = await response.json();
                    } catch (error) {
                        console.error('Error loading brands:', error);
                    }
                },

                async loadStats() {
                    try {
                        const response = await fetch('/api/dashboard');
                        this.stats = await response.json();
                    } catch (error) {
                        console.error('Error loading stats:', error);
                    }
                },

                async loadRecentActivity() {
                    try {
                        const response = await fetch('/api/forecast/runs');
                        const data = await response.json();
                        this.recentActivity = data.runs || [];
                    } catch (error) {
                        console.error('Error loading recent activity:', error);
                    }
                },

                async login() {
                    try {
                        const response = await fetch('/api/auth/login', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(this.loginForm)
                        });
                        
                        if (response.ok) {
                            const data = await response.json();
                            this.user = data;
                            this.loginForm = { username: '', password: '' };
                            await this.loadStats();
                            await this.loadRecentActivity();
                        } else {
                            alert('Login failed. Please check your credentials.');
                        }
                    } catch (error) {
                        console.error('Login error:', error);
                        alert('Login failed. Please try again.');
                    }
                },

                logout() {
                    this.user = null;
                    this.currentForecast = null;
                },

                async createForecast() {
                    try {
                        const response = await fetch('/api/forecast', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(this.forecastForm)
                        });
                        
                        if (response.ok) {
                            this.currentForecast = await response.json();
                            this.drawForecastChart();
                            await this.loadRecentActivity();
                            await this.loadStats();
                        } else {
                            alert('Forecast creation failed. Please try again.');
                        }
                    } catch (error) {
                        console.error('Forecast error:', error);
                        alert('Forecast creation failed. Please try again.');
                    }
                },

                drawForecastChart() {
                    if (!this.currentForecast) return;
                    
                    const ctx = document.getElementById('forecastChart');
                    if (!ctx) return;
                    
                    const chart = new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: this.currentForecast.points.map(p => `Week ${p.step}`),
                            datasets: [{
                                label: 'Forecast',
                                data: this.currentForecast.points.map(p => p.yhat),
                                borderColor: 'rgb(59, 130, 246)',
                                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                                tension: 0.1
                            }, {
                                label: 'Upper Bound',
                                data: this.currentForecast.points.map(p => p.yhat_upper),
                                borderColor: 'rgb(34, 197, 94)',
                                backgroundColor: 'rgba(34, 197, 94, 0.1)',
                                borderDash: [5, 5],
                                tension: 0.1
                            }, {
                                label: 'Lower Bound',
                                data: this.currentForecast.points.map(p => p.yhat_lower),
                                borderColor: 'rgb(239, 68, 68)',
                                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                                borderDash: [5, 5],
                                tension: 0.1
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                title: {
                                    display: true,
                                    text: `${this.currentForecast.brand_id} - ${this.currentForecast.model_type.toUpperCase()} Forecast (${this.currentForecast.accuracy}% accuracy)`
                                }
                            },
                            scales: {
                                y: {
                                    beginAtZero: false,
                                    title: {
                                        display: true,
                                        text: 'Demand Units'
                                    }
                                },
                                x: {
                                    title: {
                                        display: true,
                                        text: 'Time Period'
                                    }
                                }
                            }
                        }
                    });
                },

                async handleFileUpload(event) {
                    const file = event.target.files[0];
                    if (!file) return;
                    
                    const formData = new FormData();
                    formData.append('file', file);
                    formData.append('brand_id', this.forecastForm.brand_id || 'BRAND_A');
                    
                    try {
                        const response = await fetch('/api/upload/demand', {
                            method: 'POST',
                            body: formData
                        });
                        
                        if (response.ok) {
                            const data = await response.json();
                            this.uploadStatus = data.message;
                            setTimeout(() => this.uploadStatus = '', 5000);
                        } else {
                            this.uploadStatus = 'Upload failed. Please try again.';
                        }
                    } catch (error) {
                        console.error('Upload error:', error);
                        this.uploadStatus = 'Upload failed. Please try again.';
                    }
                }
            }
        }
    </script>
</body>
</html>
    """

# API Endpoints
@app.get("/", response_class=HTMLResponse)
def get_main_page():
    return get_main_page()

@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    }

@app.get("/api/brands")
def get_brands():
    return MOCK_BRANDS

@app.post("/api/auth/login")
def login(request: LoginRequest):
    if request.username in MOCK_USERS and MOCK_USERS[request.username]["password"] == request.password:
        user = MOCK_USERS[request.username]
        return {
            "access_token": f"jwt_{request.username}_{int(datetime.now().timestamp())}",
            "token_type": "bearer",
            "user_id": request.username,
            "username": request.username,
            "role": user["role"],
            "brands": user["brands"],
            "expires_in": 3600
        }
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/api/forecast", response_model=ForecastResponse)
def create_forecast(request: ForecastRequest):
    if request.brand_id not in [b["id"] for b in MOCK_BRANDS]:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    if request.model_type not in ["arima", "xgboost", "prophet", "lstm"]:
        raise HTTPException(status_code=400, detail="Invalid model type")
    
    # Generate forecast
    points = generate_mock_forecast(request.brand_id, request.horizon, request.model_type)
    accuracy = calculate_accuracy(points)
    
    # Store run
    run_id = f"run_{len(forecast_runs) + 1}_{int(datetime.now().timestamp())}"
    forecast_runs.append({
        "run_id": run_id,
        "brand_id": request.brand_id,
        "model_type": request.model_type,
        "horizon": request.horizon,
        "created_at": datetime.now().isoformat(),
        "status": "completed",
        "accuracy": accuracy
    })
    
    return ForecastResponse(
        brand_id=request.brand_id,
        model_type=request.model_type,
        horizon=request.horizon,
        points=points,
        created_at=datetime.now().isoformat(),
        accuracy=accuracy
    )

@app.get("/api/forecast/runs")
def get_forecast_runs():
    return {"runs": forecast_runs[-10:]}

@app.get("/api/dashboard")
def get_dashboard():
    total_runs = len(forecast_runs)
    successful_runs = len([r for r in forecast_runs if r["status"] == "completed"])
    avg_accuracy = np.mean([r["accuracy"] for r in forecast_runs]) if forecast_runs else 0
    
    return {
        "total_brands": len(MOCK_BRANDS),
        "total_runs": total_runs,
        "successful_runs": successful_runs,
        "avg_accuracy": round(avg_accuracy, 1),
        "top_performing_brand": random.choice([b["name"] for b in MOCK_BRANDS])
    }

@app.post("/api/upload/demand")
async def upload_demand_data(
    file: UploadFile = File(...),
    brand_id: str = Form(...)
):
    if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="File must be CSV or Excel format")
    
    records_processed = random.randint(100, 1000)
    
    upload_history.append({
        "filename": file.filename,
        "brand_id": brand_id,
        "records_processed": records_processed,
        "uploaded_at": datetime.now().isoformat(),
        "status": "success"
    })
    
    return {
        "success": True,
        "message": f"Successfully uploaded {records_processed} demand records for {brand_id}",
        "records_processed": records_processed,
        "filename": file.filename
    }

if __name__ == "__main__":
    print("🚀 Starting Pharma Forecasting Platform with Beautiful UI...")
    print("=" * 60)
    print("🌐 Web Application: http://localhost:8000")
    print("📊 Interactive Dashboard with Charts")
    print("🔑 Login: admin/password")
    print("=" * 60)
    print("✅ Features:")
    print("   • Modern, responsive UI with Tailwind CSS")
    print("   • Interactive charts and visualizations")
    print("   • Drag-and-drop file upload")
    print("   • Real-time dashboard updates")
    print("   • Professional pharma industry design")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
