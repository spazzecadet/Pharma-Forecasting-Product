from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Pharma Forecasting API",
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

@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0.0"}

@app.get("/")
def root():
    return {"message": "Pharma Forecasting API is running!", "version": "2.0.0"}

@app.get("/test")
def test():
    return {"message": "API is working!", "endpoints": [
        "/health - Health check",
        "/test - This test endpoint",
        "/docs - API documentation"
    ]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("simple_main:app", host="0.0.0.0", port=8000, reload=True)
