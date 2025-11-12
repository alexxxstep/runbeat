"""
User API schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict


class UserPreferences(BaseModel):
    """User preferences model."""

    top_genres: List[str] = Field(
        default_factory=list, description="User's top genres"
    )
    top_artists: List[str] = Field(
        default_factory=list, description="User's top artist IDs"
    )
    avg_bpm: int = Field(default=145, ge=60, le=200, description="Average BPM preference")

    class Config:
        json_schema_extra = {
            "example": {
                "top_genres": ["pop", "rock", "electronic"],
                "top_artists": ["artist_id_1", "artist_id_2"],
                "avg_bpm": 145,
            }
        }


class UserPreferencesResponse(BaseModel):
    """Response schema for user preferences."""

    user_id: str = Field(..., description="User ID")
    preferences: UserPreferences = Field(..., description="User preferences")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "uuid-here",
                "preferences": {
                    "top_genres": ["pop", "rock"],
                    "top_artists": ["artist_id_1"],
                    "avg_bpm": 145,
                },
            }
        }


class UserPreferencesUpdateRequest(BaseModel):
    """Request schema for updating user preferences."""

    preferences: UserPreferences = Field(..., description="Updated preferences")

    class Config:
        json_schema_extra = {
            "example": {
                "preferences": {
                    "top_genres": ["pop", "rock", "electronic"],
                    "top_artists": ["artist_id_1", "artist_id_2"],
                    "avg_bpm": 150,
                },
            }
        }

