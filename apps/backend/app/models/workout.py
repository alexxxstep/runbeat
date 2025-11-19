"""
Workout Pydantic models.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal


class Workout(BaseModel):
    """Workout model with parameters."""

    id: Optional[str] = Field(None, description="Workout ID (if saved in database)")
    type: Literal["steady", "progressive", "intervals", "fartlek"] = Field(
        ..., description="Type of workout"
    )
    duration_minutes: int = Field(..., gt=0, description="Duration in minutes")
    intensity: Literal["low", "moderate", "high"] = Field(
        ..., description="Workout intensity level"
    )
    hr_zones: List[int] = Field(
        default=[110, 180],
        min_length=2,
        max_length=2,
        description="Heart rate zones [min, max]",
    )
    prompt: Optional[str] = Field(
        default=None,
        description="Optional music/style prompt describing atmosphere or extra wishes",
    )
    confidence: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Confidence score (0-1)"
    )
    needs_clarification: bool = Field(
        default=False, description="Whether clarification is needed"
    )
    clarification_question: Optional[str] = Field(
        default=None, description="Question to ask user if clarification needed"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "type": "intervals",
                "duration_minutes": 40,
                "intensity": "moderate",
                "hr_zones": [130, 180],
                "confidence": 0.8,
                "needs_clarification": True,
                "clarification_question": "Який буде інтервал роботи/відпочинку?",
            }
        }

