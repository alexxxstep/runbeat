"""
Spotify API schemas.
"""
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional


class RecommendationRequest(BaseModel):
    """Request schema for Spotify recommendations."""

    seed_artists: Optional[List[str]] = Field(
        None,
        max_length=5,
        description="List of Spotify artist IDs (max 5)"
    )
    seed_tracks: Optional[List[str]] = Field(
        None,
        max_length=5,
        description="List of Spotify track IDs (max 5)"
    )
    seed_genres: Optional[List[str]] = Field(
        None,
        max_length=5,
        description="List of seed genres (max 5)"
    )
    limit: int = Field(
        20,
        ge=1,
        le=100,
        description="Number of recommendations (1-100, default 20)"
    )
    market: str = Field(
        "US",
        description="ISO country code (default 'US')"
    )
    # Energy filters
    min_energy: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Minimum energy (0-1)"
    )
    max_energy: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Maximum energy (0-1)"
    )
    target_energy: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Target energy (0-1)"
    )
    # Tempo filters
    min_tempo: Optional[float] = Field(
        None,
        ge=0.0,
        le=250.0,
        description="Minimum tempo/BPM (0-250)"
    )
    max_tempo: Optional[float] = Field(
        None,
        ge=0.0,
        le=250.0,
        description="Maximum tempo/BPM (0-250)"
    )
    target_tempo: Optional[float] = Field(
        None,
        ge=0.0,
        le=250.0,
        description="Target tempo/BPM (0-250)"
    )
    # Danceability filters
    min_danceability: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Minimum danceability (0-1)"
    )
    max_danceability: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Maximum danceability (0-1)"
    )
    # Valence filters
    min_valence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Minimum valence (0-1)"
    )
    max_valence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Maximum valence (0-1)"
    )
    # Acousticness filters
    min_acousticness: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Minimum acousticness (0-1)"
    )
    max_acousticness: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Maximum acousticness (0-1)"
    )
    # Phase (for workout context)
    phase: Optional[str] = Field(
        None,
        description="Workout phase: 'warm-up', 'main', or 'cool-down'"
    )

    @field_validator("seed_artists", "seed_tracks", "seed_genres")
    @classmethod
    def validate_seeds_not_empty(cls, v):
        """Ensure seed lists don't contain empty strings."""
        if v is not None:
            return [s for s in v if s and s.strip()]
        return v

    @field_validator("phase")
    @classmethod
    def validate_phase(cls, v):
        """Validate phase value."""
        if v is not None and v not in ["warm-up", "main", "cool-down"]:
            raise ValueError(
                "phase must be one of: 'warm-up', 'main', 'cool-down'"
            )
        return v

    @model_validator(mode="after")
    def validate_at_least_one_seed(self):
        """Validate that at least one seed is provided."""
        has_seeds = (
            (self.seed_artists and len(self.seed_artists) > 0) or
            (self.seed_tracks and len(self.seed_tracks) > 0) or
            (self.seed_genres and len(self.seed_genres) > 0)
        )
        if not has_seeds:
            raise ValueError(
                "At least one of seed_artists, seed_tracks, or "
                "seed_genres must be provided"
            )
        return self

    class Config:
        json_schema_extra = {
            "example": {
                "seed_genres": ["electronic", "house"],
                "seed_tracks": ["4iV5W9uYEdYUVa79Axb7Rh"],
                "limit": 20,
                "min_tempo": 120,
                "max_tempo": 140,
                "min_energy": 0.6,
                "target_energy": 0.7,
                "phase": "main"
            }
        }


class RecommendationTrack(BaseModel):
    """Single recommendation track schema."""

    id: str = Field(..., description="Spotify track ID")
    name: str = Field(..., description="Track name")
    artists: List[str] = Field(..., description="List of artist names")
    tempo: Optional[float] = Field(None, description="Tempo/BPM")
    energy: Optional[float] = Field(None, description="Energy level (0-1)")
    danceability: Optional[float] = Field(
        None, description="Danceability (0-1)"
    )
    duration_ms: int = Field(..., description="Duration in milliseconds")
    popularity: Optional[int] = Field(None, description="Popularity (0-100)")
    uri: str = Field(..., description="Spotify track URI")
    preview_url: Optional[str] = Field(
        None, description="Preview URL (30-second clip)"
    )
    phase: Optional[str] = Field(
        None, description="Workout phase"
    )
    seed_type: str = Field(
        "recommendation", description="Seed type"
    )
    seed_name: str = Field(
        "Spotify Recommendations", description="Seed name"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "4iV5W9uYEdYUVa79Axb7Rh",
                "name": "Song Name",
                "artists": ["Artist 1", "Artist 2"],
                "tempo": 175.5,
                "energy": 0.75,
                "danceability": 0.8,
                "duration_ms": 210000,
                "popularity": 85,
                "uri": "spotify:track:4iV5W9uYEdYUVa79Axb7Rh",
                "preview_url": "https://p.scdn.co/mp3-preview/...",
                "phase": "main",
                "seed_type": "recommendation",
                "seed_name": "Spotify Recommendations"
            }
        }


class RecommendationResponse(BaseModel):
    """Response schema for Spotify recommendations."""

    status: str = Field(..., description="Response status")
    count: int = Field(..., description="Number of recommendations")
    recommendations: List[RecommendationTrack] = Field(
        ..., description="List of recommended tracks"
    )
    message: Optional[str] = Field(
        None, description="Error or info message"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "count": 20,
                "recommendations": [],
                "message": None
            }
        }

