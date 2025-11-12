"""
Authentication API schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional


class SpotifyAuthResponse(BaseModel):
    """Response schema for Spotify authentication."""

    auth_url: str = Field(..., description="Spotify OAuth authorization URL")
    state: str = Field(..., description="OAuth state for CSRF protection")

    class Config:
        json_schema_extra = {
            "example": {
                "auth_url": "https://accounts.spotify.com/authorize?...",
                "state": "random_state_string",
            }
        }


class SpotifyCallbackResponse(BaseModel):
    """Response schema for Spotify OAuth callback."""

    success: bool = Field(..., description="Whether authentication was successful")
    user_id: Optional[str] = Field(None, description="User ID in database")
    spotify_user_id: Optional[str] = Field(None, description="Spotify user ID")
    message: str = Field(..., description="Response message")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "user_id": "uuid-here",
                "spotify_user_id": "spotify_user_123",
                "message": "Successfully authenticated with Spotify",
            }
        }

