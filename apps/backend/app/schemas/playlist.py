"""
Playlist API schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from app.models.workout import Workout


class IntervalStage(BaseModel):
    """Interval stage schema."""

    name: str = Field(..., description="Stage name")
    duration_minutes: float = Field(...,
                                    description="Stage duration in minutes")
    hr_zone: List[int] = Field(
        ..., min_length=2, max_length=2, description="Heart rate zone [min, max]"
    )
    bpm_range: List[int] = Field(
        ..., min_length=2, max_length=2, description="BPM range [min, max]"
    )


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
    user_id: Optional[str] = Field(
        None, description="User ID (optional, for creating Spotify playlist)"
    )
    workout_id: Optional[str] = Field(
        None, description="Existing workout ID (optional, to reuse existing workout instead of creating new one)"
    )
    interval_stages: Optional[List[IntervalStage]] = Field(
        None, description="Custom interval stages (for intervals workout type)"
    )
    prompt: Optional[str] = Field(
        None, description="User prompt for track search refinement"
    )
    excluded_track_ids: Optional[List[str]] = Field(
        None, description="List of track IDs to exclude from generation (e.g., from previous variants)"
    )
    selected_tracks: Optional[List[Dict]] = Field(
        None, description="Pre-selected tracks from variant to use directly (bypasses generation)"
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

    playlist_id: Optional[str] = Field(
        None, description="Playlist ID (if saved)")
    spotify_url: Optional[str] = Field(
        None, description="Spotify playlist URL")
    playlist_name: Optional[str] = Field(
        None, description="Playlist name (if created in Spotify)")
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


class TrackVariant(BaseModel):
    """Single track variant schema."""

    tracks: list = Field(..., description="List of tracks")
    total_duration: float = Field(..., description="Total duration in seconds")
    total_tracks: int = Field(..., description="Number of tracks")


class PlaylistVariantsResponse(BaseModel):
    """Response schema for playlist variants preview."""

    variant1: TrackVariant = Field(..., description="First track variant")
    variant2: TrackVariant = Field(..., description="Second track variant")
    generation_time_seconds: float = Field(
        ..., description="Time taken to generate variants"
    )
