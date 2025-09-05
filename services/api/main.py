from fastapi import FastAPI
from routers import baseline


app = FastAPI(title="Pharma Forecasting API", version="0.1.0")


@app.get("/health")
def health():
	return {"status": "ok"}

app.include_router(baseline.router)


if __name__ == "__main__":
	# Allows: python services/api/main.py (development only)
	import uvicorn
	uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

