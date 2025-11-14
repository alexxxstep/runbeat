"""
Pydantic models for LLM structured outputs.
"""
from pydantic import BaseModel, Field
from typing import List, Literal, Optional


class IntervalPhase(BaseModel):
    """Interval phase for interval and fartlek workouts."""

    type: Literal["work", "rest"] = Field(..., description="Phase type: work or rest")
    duration_minutes: int = Field(..., ge=1, le=60, description="Duration in minutes")
    target_bpm: int = Field(..., ge=80, le=200, description="Target BPM for this phase")


class WorkoutIntent(BaseModel):
    """Parsed workout intent from user message."""

    workout_type: Literal["continuous", "intervals", "fartlek", "recovery"] = Field(
        ..., description="Type of workout"
    )
    duration_minutes: int = Field(
        ..., ge=5, le=180, description="Total workout duration in minutes"
    )
    target_bpm_min: int = Field(
        ..., ge=80, le=200, description="Minimum target BPM"
    )
    target_bpm_max: int = Field(
        ..., ge=80, le=200, description="Maximum target BPM"
    )
    intervals: Optional[List[IntervalPhase]] = Field(
        default=None,
        description="Interval phases (required for intervals and fartlek workouts)",
    )
    energy_profile: Literal["steady", "building", "wave"] = Field(
        default="steady", description="Energy profile of the workout"
    )
    mood: Optional[str] = Field(
        default=None, description="Mood or emotional context of the workout"
    )
    music_genres: Optional[List[str]] = Field(
        default=None,
        description="Requested music genres (e.g., ['rock', 'electronic', 'hip-hop']). Extract from user message if mentioned."
    )
    music_prompt: Optional[str] = Field(
        default=None,
        description="User's description of desired music style, mood, or characteristics (e.g., 'мотивуюча музика', 'агресивний рок', 'спокійна електроніка'). Extract from user message if mentioned."
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score for the parsed intent"
    )
    needs_clarification: bool = Field(
        default=False, description="Whether clarification is needed from the user"
    )
    clarification_question: Optional[str] = Field(
        default=None, description="Question to ask if clarification is needed"
    )

    def to_workout(self) -> "Workout":
        """
        Convert WorkoutIntent to Workout model.

        Returns:
            Workout model instance
        """
        from app.models.workout import Workout

        # Map workout_type to Workout.type
        workout_type_map = {
            "continuous": "steady",
            "intervals": "intervals",
            "fartlek": "fartlek",
            "recovery": "steady",
        }
        workout_type = workout_type_map.get(self.workout_type, "steady")

        # Map energy_profile to progressive if building, otherwise use mapped type
        if self.energy_profile == "building" and workout_type == "steady":
            workout_type = "progressive"

        # Derive intensity from target BPM
        # Low: 80-130, Moderate: 130-160, High: 160-200
        avg_bpm = (self.target_bpm_min + self.target_bpm_max) / 2
        if avg_bpm < 130:
            intensity = "low"
        elif avg_bpm < 160:
            intensity = "moderate"
        else:
            intensity = "high"

        return Workout(
            type=workout_type,
            duration_minutes=self.duration_minutes,
            intensity=intensity,
            hr_zones=[self.target_bpm_min, self.target_bpm_max],
            confidence=self.confidence,
            needs_clarification=self.needs_clarification,
            clarification_question=self.clarification_question,
        )

    class Config:
        json_schema_extra = {
            "example": {
                "workout_type": "intervals",
                "duration_minutes": 40,
                "target_bpm_min": 130,
                "target_bpm_max": 180,
                "intervals": [
                    {"type": "work", "duration_minutes": 3, "target_bpm": 170},
                    {"type": "rest", "duration_minutes": 2, "target_bpm": 120},
                ],
                "energy_profile": "wave",
                "mood": "energetic",
                "music_genres": ["rock", "electronic"],
                "music_prompt": "мотивуюча музика",
                "confidence": 0.85,
                "needs_clarification": False,
            }
        }


class PlaylistTrack(BaseModel):
    """Track in playlist response."""

    title: str = Field(..., description="Track title")
    artist: str = Field(..., description="Artist name")
    bpm: float = Field(..., description="BPM (tempo)")
    duration_seconds: float = Field(..., description="Duration in seconds")
    energy_level: float = Field(..., ge=0.0, le=1.0, description="Energy level (0-1)")
    genre: str = Field(..., description="Primary genre")
    phase: Literal["warm-up", "main", "cool-down"] = Field(
        ..., description="Workout phase"
    )


class PlaylistResponse(BaseModel):
    """Response schema for playlist generation from LLM."""

    playlist_name: str = Field(..., description="Playlist name")
    total_tracks: int = Field(..., ge=1, description="Total number of tracks")
    total_duration_minutes: float = Field(..., ge=0, description="Total duration in minutes")
    bpm_range: List[int] = Field(
        ..., min_length=2, max_length=2, description="BPM range [min, max]"
    )
    progression_type: Literal["steady", "building", "wave", "pyramid"] = Field(
        ..., description="BPM progression type"
    )
    primary_genres: List[str] = Field(..., description="Primary genres in playlist")
    tracks: List[PlaylistTrack] = Field(..., description="List of tracks")
    curation_notes: Optional[str] = Field(
        None, description="Curation notes explaining choices"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "playlist_name": "Tempo Tuesday",
                "total_tracks": 12,
                "total_duration_minutes": 41.0,
                "bpm_range": [120, 160],
                "progression_type": "building",
                "primary_genres": ["house", "techno"],
                "tracks": [],
                "curation_notes": "Warm-up gradually builds from 120→140 BPM...",
            }
        }

