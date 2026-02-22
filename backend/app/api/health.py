"""
app/api/health.py — Health check endpoint.

PHASE 1 CHECKPOINT:
  GET /health  →  {"status": "ok", "version": "1.0.0", ...}
"""
from fastapi import APIRouter
from pydantic import BaseModel
from app.config import get_settings

router = APIRouter()
settings = get_settings()


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    model: str


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Returns 200 if the service is running. Used by GCP Cloud Run."""
    return HealthResponse(
        status="ok",
        version="1.0.0",
        environment=settings.app_env,
        model=settings.groq_model,
    )
