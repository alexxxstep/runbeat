"""
Chat API schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from app.models.workout import Workout


class ChatRequest(BaseModel):
    """Request schema for chat message."""

    message: str = Field(..., min_length=1, description="User message")
    user_id: Optional[str] = Field(None, description="User ID (optional)")
    conversation_id: Optional[str] = Field(
        None, description="Conversation ID for multi-turn conversations"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Хочу пробігти 40 хв з інтервалами",
                "user_id": None,
                "conversation_id": None,
            }
        }


class ChatResponse(BaseModel):
    """Response schema for chat message."""

    message: str = Field(..., description="AI response message")
    workout: Optional[Workout] = Field(None, description="Parsed workout (if available)")
    playlist: Optional[Dict[str, Any]] = Field(
        None, description="Generated playlist (if available and complete)"
    )
    needs_clarification: bool = Field(
        default=False, description="Whether clarification is needed"
    )
    conversation_id: Optional[str] = Field(
        None, description="Conversation ID for continuing the conversation"
    )
    is_complete: bool = Field(
        default=False, description="Whether the workout spec is complete and ready for playlist generation"
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
                "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
                "is_complete": True,
            }
        }

