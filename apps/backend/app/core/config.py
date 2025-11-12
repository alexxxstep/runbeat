"""
Application configuration using Pydantic Settings.
"""
import os
from pydantic_settings import BaseSettings
from typing import List, Optional


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
    OPENAI_MODEL: str = "gpt-4"

    # App Settings
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:19006"]

    # Railway/Deployment
    PORT: int = 8000
    RAILWAY_PUBLIC_DOMAIN: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
_settings = Settings()

# Auto-detect Railway URL and set redirect URI if not provided
if not _settings.SPOTIFY_REDIRECT_URI:
    if _settings.RAILWAY_PUBLIC_DOMAIN:
        _settings.SPOTIFY_REDIRECT_URI = f"https://{_settings.RAILWAY_PUBLIC_DOMAIN}/auth/spotify/callback"
    elif _settings.ENVIRONMENT == "production":
        # Try to get from Railway environment variables
        railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN") or os.getenv("RAILWAY_STATIC_URL")
        if railway_domain:
            _settings.SPOTIFY_REDIRECT_URI = f"https://{railway_domain}/auth/spotify/callback"
        else:
            # Fallback - user must set manually in Railway Variables
            _settings.SPOTIFY_REDIRECT_URI = "http://localhost:8000/auth/spotify/callback"
    else:
        _settings.SPOTIFY_REDIRECT_URI = f"http://localhost:{_settings.PORT}/auth/spotify/callback"

settings = _settings

