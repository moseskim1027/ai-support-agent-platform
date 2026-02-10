"""Health check endpoints"""

from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    timestamp: datetime
    version: str


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint

    Returns:
        HealthResponse: Service health status
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="0.1.0"
    )


@router.get("/ready")
async def readiness_check():
    """
    Readiness check endpoint for Kubernetes

    Returns:
        dict: Service readiness status
    """
    # TODO: Check database, vector store, and other dependencies
    return {"status": "ready"}


@router.get("/live")
async def liveness_check():
    """
    Liveness check endpoint for Kubernetes

    Returns:
        dict: Service liveness status
    """
    return {"status": "alive"}
