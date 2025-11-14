"""
RunBeat Backend - FastAPI Application Entry Point
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.core.config import settings
from app.api.routes import health, chat, playlists, auth, workouts, users, error_logs

# Configure logger
log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
os.makedirs(log_dir, exist_ok=True)
logger.add(
    os.path.join(log_dir, "runbeat_{time}.log"),
    rotation="1 day",
    retention="7 days",
    level=settings.LOG_LEVEL,
)

# Add database log handler for errors
try:
    from app.utils.database_log_handler import DatabaseLogHandler
    logger.add(
        DatabaseLogHandler(min_level="ERROR"),
        level="ERROR",
        format="{time} | {level} | {message}",
        filter=lambda record: record["level"].name in ["ERROR", "CRITICAL", "WARNING"],
    )
    logger.info("Database log handler added successfully")
except Exception as e:
    logger.warning(f"Failed to add database log handler: {e}. Errors will only be logged to file.")

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

# Include routers with API versioning
# Health check endpoints (no versioning)
app.include_router(health.router, tags=["health"])

# API v1 endpoints
api_v1_prefix = "/api/v1"
app.include_router(chat.router, prefix=api_v1_prefix, tags=["chat"])
app.include_router(playlists.router, prefix=api_v1_prefix, tags=["playlists"])
app.include_router(auth.router, prefix=api_v1_prefix, tags=["auth"])
app.include_router(workouts.router, prefix=api_v1_prefix, tags=["workouts"])
app.include_router(users.router, prefix=api_v1_prefix, tags=["users"])
app.include_router(error_logs.router, prefix=api_v1_prefix, tags=["error-logs"])

# Backward compatibility: also include without prefix for existing clients
# TODO: Remove in future version
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

    # Test error logging service
    try:
        from app.services.error_logging_service import error_logging_service
        logger.info("Error logging service is ready")
    except Exception as e:
        logger.error(f"Error logging service initialization failed: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("RunBeat API shutting down")
