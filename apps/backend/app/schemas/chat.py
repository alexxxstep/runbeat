"""
Chat API schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional
from app.models.workout import Workout


class ChatRequest(BaseModel):
    """Request schema for chat message."""

    message: str = Field(..., min_length=1, description="User message")
    user_id: Optional[str] = Field(None, description="User ID (optional)")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Хочу пробігти 40 хв з інтервалами",
                "user_id": None,
            }
        }


class ChatResponse(BaseModel):
    """Response schema for chat message."""

    message: str = Field(..., description="AI response message")
    workout: Optional[Workout] = Field(None, description="Parsed workout (if available)")
    needs_clarification: bool = Field(
        default=False, description="Whether clarification is needed"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Зрозумів! Генерую плейлист на 40 хв...",
                "workout": {
                    "type": "intervals",
                    "duration_minutes": 40,
                    "intensity": "moderate",
                    "hr_zones": [130, 180],
                    "confidence": 0.8,
                    "needs_clarification": False,
                },
                "needs_clarification": False,
            }
        }

