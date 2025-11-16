"""
Application configuration using Pydantic Settings.
"""
import os
import json
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Optional, Union
from loguru import logger


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Supabase
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_KEY: str

    # Spotify OAuth
    SPOTIFY_CLIENT_ID: str
    SPOTIFY_CLIENT_SECRET: str
    SPOTIFY_REDIRECT_URI: Optional[str] = None

    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4"  # Default model for all agents

    # Optional: Different models for different agents (falls back to OPENAI_MODEL if not set)
    OPENAI_MODEL_PARSER: Optional[str] = None  # Model for parser tools/agents
    OPENAI_MODEL_CONVERSATION: Optional[str] = None  # Model for ConversationAgent (WorkoutBuilder)
    OPENAI_MODEL_SUPERVISOR: Optional[str] = None  # Model for SupervisorAgent

    # LangChain Feature Flags (all enabled by default - migration complete)
    USE_LANGCHAIN_PARSER: bool = True  # Use LangChain parser tools (default: enabled)
    USE_LANGCHAIN_SUPERVISOR: bool = True  # Use LangChain Supervisor (default: enabled)

    # App Settings
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000", "http://localhost:19006"]
    FRONTEND_URL: Optional[str] = None  # Production frontend URL

    # Railway/Deployment
    PORT: int = 8000
    RAILWAY_PUBLIC_DOMAIN: Optional[str] = None

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[List[str], str]) -> List[str]:
        """Parse CORS_ORIGINS from JSON string or comma-separated string."""
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            # Try parsing as JSON first
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except (json.JSONDecodeError, TypeError):
                pass

            # If not JSON, try comma-separated
            if "," in v:
                return [origin.strip() for origin in v.split(",")]

            # Single string
            return [v.strip()]
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
_settings = Settings()

# Auto-detect and add production frontend URL to CORS if in production
if _settings.ENVIRONMENT == "production":
    # Try to get frontend URL from environment or Railway
    frontend_url = (
        _settings.FRONTEND_URL
        or os.getenv("FRONTEND_URL")
        or os.getenv("RAILWAY_STATIC_URL")
    )

    # Ensure CORS_ORIGINS is a list
    if isinstance(_settings.CORS_ORIGINS, str):
        _settings.CORS_ORIGINS = [_settings.CORS_ORIGINS]
    elif not isinstance(_settings.CORS_ORIGINS, list):
        _settings.CORS_ORIGINS = list(_settings.CORS_ORIGINS)

    # Add frontend URL if found
    if frontend_url and frontend_url not in _settings.CORS_ORIGINS:
        _settings.CORS_ORIGINS.append(frontend_url)
        logger.info(f"Added frontend URL to CORS: {frontend_url}")

    # Also add common production URLs
    production_urls = [
        "https://runbeatweb-production.up.railway.app",
        "https://runbeatweb-production.railway.app",
    ]
    for url in production_urls:
        if url not in _settings.CORS_ORIGINS:
            _settings.CORS_ORIGINS.append(url)

# Auto-detect Railway URL and set redirect URI if not provided
if not _settings.SPOTIFY_REDIRECT_URI:
    if _settings.RAILWAY_PUBLIC_DOMAIN:
        _settings.SPOTIFY_REDIRECT_URI = f"https://{_settings.RAILWAY_PUBLIC_DOMAIN}/auth/spotify/callback"
    elif _settings.ENVIRONMENT == "production":
        # Try to get from Railway environment variables
        railway_domain = os.getenv(
            "RAILWAY_PUBLIC_DOMAIN") or os.getenv("RAILWAY_STATIC_URL")
        if railway_domain:
            _settings.SPOTIFY_REDIRECT_URI = f"https://{railway_domain}/auth/spotify/callback"
        else:
            # Fallback - user must set manually in Railway Variables
            _settings.SPOTIFY_REDIRECT_URI = "http://localhost:8000/auth/spotify/callback"
    else:
        _settings.SPOTIFY_REDIRECT_URI = f"http://localhost:{_settings.PORT}/auth/spotify/callback"

settings = _settings

# Log CORS settings on startup
logger.info(f"CORS_ORIGINS configured: {settings.CORS_ORIGINS}")

# Log Spotify redirect URI for debugging
if settings.SPOTIFY_REDIRECT_URI:
    logger.info(
        f"SPOTIFY_REDIRECT_URI configured: {settings.SPOTIFY_REDIRECT_URI}")
else:
    logger.warning(
        "SPOTIFY_REDIRECT_URI not set! "
        "Please set it in Railway Variables or .env file"
    )
