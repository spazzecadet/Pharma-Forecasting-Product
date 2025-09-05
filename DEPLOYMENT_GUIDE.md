# 🚀 Pharma Forecasting Platform - Deployment Guide

## 🌐 **Live Demo Access**

### **Option 1: Railway (Recommended - Free)**
1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your `Pharma-Forecasting-Product` repository
5. Railway will automatically deploy your app
6. Get your live URL (e.g., `https://your-app-name.railway.app`)

### **Option 2: Render (Free Tier)**
1. Go to [render.com](https://render.com)
2. Sign up with GitHub
3. Click "New" → "Web Service"
4. Connect your GitHub repository
5. Use these settings:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python3 complete_pharma_platform.py`
   - **Health Check Path:** `/api/health`
6. Deploy and get your live URL

### **Option 3: Heroku (Free Tier)**
1. Go to [heroku.com](https://heroku.com)
2. Create a new app
3. Connect to GitHub repository
4. Enable automatic deploys
5. Deploy and get your live URL

## 🔧 **Local Development**

### **Quick Start:**
```bash
# Clone the repository
git clone https://github.com/spazzecadet/Pharma-Forecasting-Product.git
cd Pharma-Forecasting-Product

# Install dependencies
pip install -r requirements.txt

# Run the application
python3 complete_pharma_platform.py

# Access at http://localhost:8000
```

## 📱 **Demo Instructions**

### **Login Credentials:**
- **Admin:** `admin` / `password`
- **Analyst:** `analyst` / `analyst123`
- **Viewer:** `viewer` / `viewer123`

### **Features to Demo:**
1. **Dashboard:** View statistics and brand performance
2. **Forecasting:** Create forecasts with different ML models
3. **Scenarios:** Run price impact analysis
4. **Upload:** Test file upload functionality
5. **Monitoring:** Check model drift detection

## 🎯 **For Stakeholders**

### **Share This Link:**
Once deployed, share your live URL with:
- **Product Overview:** Interactive dashboard
- **Forecasting Capabilities:** Multiple ML models
- **Scenario Analysis:** Price impact testing
- **Data Management:** File upload and validation
- **Model Monitoring:** Drift detection and performance tracking

### **Key Features to Highlight:**
- ✅ **Professional UI/UX** - Looks like enterprise software
- ✅ **Interactive Charts** - Real-time visualizations
- ✅ **Multiple ML Models** - ARIMA, XGBoost, Prophet, LSTM
- ✅ **Scenario Analysis** - "What-if" price impact testing
- ✅ **File Upload** - CSV/Excel data ingestion
- ✅ **Model Monitoring** - Drift detection and alerts
- ✅ **Role-based Access** - Different user permissions

## 🔗 **Repository**
**GitHub:** https://github.com/spazzecadet/Pharma-Forecasting-Product

## 📞 **Support**
For questions or issues, please refer to the repository or contact the development team.
