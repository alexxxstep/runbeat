"""
RunBeat Backend - FastAPI Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.core.config import settings
from app.api.routes import health, chat, playlists, auth, workouts, users

# Configure logger
import os
log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
os.makedirs(log_dir, exist_ok=True)
logger.add(
    os.path.join(log_dir, "runbeat_{time}.log"),
    rotation="1 day",
    retention="7 days",
    level=settings.LOG_LEVEL,
)

# Create FastAPI app
app = FastAPI(
    title="RunBeat API",
    description="AI music assistant for runners",
    version="2.0.0",
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(chat.router, tags=["chat"])
app.include_router(playlists.router, tags=["playlists"])
app.include_router(auth.router, tags=["auth"])
app.include_router(workouts.router, tags=["workouts"])
app.include_router(users.router, tags=["users"])


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info(f"RunBeat API starting in {settings.ENVIRONMENT} mode")
    logger.info(f"Log level: {settings.LOG_LEVEL}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("RunBeat API shutting down")

