"""
Workout API schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.workout import Workout


class WorkoutCreateRequest(BaseModel):
    """Request schema for creating a workout."""

    workout: Workout = Field(..., description="Workout parameters")
    user_id: str = Field(..., description="User ID")

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
                "user_id": "uuid-here",
            }
        }


class WorkoutResponse(BaseModel):
    """Response schema for workout."""

    id: str = Field(..., description="Workout ID")
    user_id: str = Field(..., description="User ID")
    type: str = Field(..., description="Workout type")
    duration_minutes: int = Field(..., description="Duration in minutes")
    intensity: str = Field(..., description="Intensity level")
    hr_zones: List[int] = Field(..., description="Heart rate zones")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "uuid-here",
                "user_id": "uuid-here",
                "type": "steady",
                "duration_minutes": 30,
                "intensity": "low",
                "hr_zones": [110, 130],
                "completed_at": None,
                "created_at": "2025-11-12T10:00:00Z",
            }
        }


class WorkoutListResponse(BaseModel):
    """Response schema for workout list."""

    workouts: List[WorkoutResponse] = Field(..., description="List of workouts")
    total: int = Field(..., description="Total number of workouts")

    class Config:
        json_schema_extra = {
            "example": {
                "workouts": [],
                "total": 0,
            }
        }

