from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from app.api.routes import router as routes
from app.logger import logger

app = FastAPI(
    title="ML Training Service",
    version="0.1",
    description="Service for training ML models with DVC and ClearML integration",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.include_router(routes)

Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

@app.get("/")
def root():
    logger.info("Root endpoint accessed")
    return {"message": "ML Training Service is up", "version": "0.1"}