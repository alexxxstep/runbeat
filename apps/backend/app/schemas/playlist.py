"""
Playlist API schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional
from app.models.workout import Workout


class PlaylistGenerateRequest(BaseModel):
    """Request schema for playlist generation."""

    workout: Workout = Field(..., description="Workout parameters")
    user_preferences: Optional[dict] = Field(
        default_factory=lambda: {
            "top_genres": [],
            "top_artists": [],
            "avg_bpm": 145,
        },
        description="User preferences (genres, artists, etc.)",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "workout": {
                    "type": "steady",
                    "duration_minutes": 30,
                    "intensity": "low",
                    "hr_zones": [110, 130],
                    "confidence": 0.95,
                    "needs_clarification": False,
                },
                "user_preferences": {
                    "top_genres": ["pop", "rock"],
                    "top_artists": ["artist_id_1", "artist_id_2"],
                    "avg_bpm": 145,
                },
            }
        }


class PlaylistGenerateResponse(BaseModel):
    """Response schema for playlist generation."""

    playlist_id: Optional[str] = Field(None, description="Playlist ID (if saved)")
    spotify_url: Optional[str] = Field(None, description="Spotify playlist URL")
    tracks: list = Field(..., description="List of tracks")
    total_duration: float = Field(..., description="Total duration in seconds")
    total_tracks: int = Field(..., description="Number of tracks")
    generation_time_seconds: Optional[float] = Field(
        None, description="Time taken to generate playlist"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "playlist_id": "playlist_123",
                "spotify_url": "https://open.spotify.com/playlist/...",
                "tracks": [],
                "total_duration": 1800.0,
                "total_tracks": 15,
                "generation_time_seconds": 8.5,
            }
        }

