"""
Playlist Pydantic models.
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class Track(BaseModel):
    """Track model with audio features."""

    id: str = Field(..., description="Spotify track ID")
    name: str = Field(..., description="Track name")
    artist: str = Field(..., description="Artist name")
    artist_id: str = Field(..., description="Spotify artist ID")
    album: Optional[str] = Field(None, description="Album name")
    duration_ms: int = Field(..., description="Duration in milliseconds")
    spotify_url: str = Field(..., description="Spotify track URL")
    spotify_uri: str = Field(..., description="Spotify track URI")
    preview_url: Optional[str] = Field(None, description="Preview URL")

    # Audio features
    tempo: float = Field(..., description="BPM (tempo)")
    bpm: float = Field(..., description="BPM (alias for tempo)")
    energy: float = Field(..., ge=0.0, le=1.0,
                          description="Energy level (0-1)")
    danceability: float = Field(
        ..., ge=0.0, le=1.0, description="Danceability (0-1)"
    )
    valence: float = Field(..., ge=0.0, le=1.0, description="Valence (0-1)")
    genres: List[str] = Field(default_factory=list, description="Genres")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "4iV5W9uYEdYUVa79Axb7Rh",
                "name": "Song Name",
                "artist": "Artist Name",
                "artist_id": "1Xyo4u8uXC1ZmMpatF05PJ",
                "album": "Album Name",
                "duration_ms": 200000,
                "spotify_url": "https://open.spotify.com/track/4iV5W9uYEdYUVa79Axb7Rh",
                "spotify_uri": "spotify:track:4iV5W9uYEdYUVa79Axb7Rh",
                "tempo": 120.0,
                "bpm": 120.0,
                "energy": 0.8,
                "danceability": 0.7,
                "valence": 0.6,
                "genres": ["pop", "rock"],
            }
        }

    def __init__(self, **data):
        """Initialize track with BPM alias."""
        if "bpm" not in data and "tempo" in data:
            data["bpm"] = data["tempo"]
        elif "tempo" not in data and "bpm" in data:
            data["tempo"] = data["bpm"]
        super().__init__(**data)


class PlaylistData(BaseModel):
    """Playlist data model."""

    tracks: List[Track] = Field(..., description="List of tracks")
    total_duration: float = Field(..., description="Total duration in seconds")
    total_tracks: int = Field(..., description="Number of tracks")

    class Config:
        json_schema_extra = {
            "example": {
                "tracks": [],
                "total_duration": 1800.0,
                "total_tracks": 15,
            }
        }

    def __init__(self, **data):
        """Initialize playlist with calculated total_tracks."""
        if "total_tracks" not in data and "tracks" in data:
            data["total_tracks"] = len(data["tracks"])
        super().__init__(**data)
