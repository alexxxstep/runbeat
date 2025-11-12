"""
Health check endpoints.
"""
from fastapi import APIRouter
from datetime import datetime
from typing import Dict

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
async def health_check() -> Dict[str, str]:
    """
    Basic health check endpoint.
    Returns API status and timestamp.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "runbeat-api",
    }


@router.get("/ready")
async def readiness_check() -> Dict[str, str]:
    """
    Readiness check endpoint.
    Verifies that the service is ready to accept traffic.
    """
    # TODO: Add database connection check
    return {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/live")
async def liveness_check() -> Dict[str, str]:
    """
    Liveness check endpoint.
    Verifies that the service is alive.
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
    }

