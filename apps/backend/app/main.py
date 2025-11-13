"""
RunBeat Backend - FastAPI Application Entry Point
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.core.config import settings
from app.api.routes import health, chat, playlists, auth, workouts, users

# Configure logger
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
# In production, also allow requests from known Railway domains
cors_origins = list(settings.CORS_ORIGINS) if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS]

# Add production frontend URLs if in production
if settings.ENVIRONMENT == "production":
    production_origins = [
        "https://runbeatweb-production.up.railway.app",
        "https://runbeatweb-production.railway.app",
    ]
    for origin in production_origins:
        if origin not in cors_origins:
            cors_origins.append(origin)

    # Also check FRONTEND_URL from environment
    frontend_url = os.getenv("FRONTEND_URL")
    if frontend_url and frontend_url not in cors_origins:
        cors_origins.append(frontend_url)

logger.info(f"CORS configured with {len(cors_origins)} origins: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
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
    logger.info(f"CORS allowed origins: {settings.CORS_ORIGINS}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("RunBeat API shutting down")
