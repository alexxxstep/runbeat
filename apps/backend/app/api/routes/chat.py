"""
Chat endpoints for LLM-powered workout parsing.
"""
from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from app.services.llm_service import LLMService
from app.schemas.chat import ChatRequest, ChatResponse
from app.models.workout import Workout

router = APIRouter(prefix="/chat", tags=["chat"])


def get_llm_service() -> LLMService:
    """Dependency to get LLMService instance."""
    return LLMService()


@router.post("/message", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    llm: LLMService = Depends(get_llm_service),
) -> ChatResponse:
    """
    Parse user message with OpenAI GPT-4.
    Extract workout parameters from natural language.

    Args:
        request: Chat request with user message
        llm: LLMService dependency

    Returns:
        ChatResponse with parsed workout or clarification question

    Raises:
        HTTPException: If parsing fails
    """
    try:
        # LLM prompt for workout extraction
        prompt = f"""
You are RunBeat AI assistant. Parse the user's workout request into structured JSON.

User message: "{request.message}"

Extract:
{{
  "type": "steady|progressive|intervals|fartlek",
  "duration_minutes": <number>,
  "intensity": "low|moderate|high",
  "hr_zones": [<min>, <max>],
  "confidence": <0-1>,
  "needs_clarification": <bool>,
  "clarification_question": "<string if needed>"
}}

Examples:
"Хочу пробігти 40 хв з інтервалами" →
{{
  "type": "intervals",
  "duration_minutes": 40,
  "intensity": "moderate",
  "hr_zones": [130, 180],
  "confidence": 0.8,
  "needs_clarification": true,
  "clarification_question": "Який буде інтервал роботи/відпочинку?"
}}

"Легке відновлення 30 хвилин" →
{{
  "type": "steady",
  "duration_minutes": 30,
  "intensity": "low",
  "hr_zones": [110, 130],
  "confidence": 0.95,
  "needs_clarification": false
}}

Return ONLY valid JSON.
"""

        # Call OpenAI
        workout_params = await llm.parse_workout(prompt)

        # Check if clarification is needed
        if workout_params.get("needs_clarification"):
            clarification_question = workout_params.get(
                "clarification_question", "Можете уточнити деталі тренування?"
            )
            return ChatResponse(
                message=clarification_question,
                workout=None,
                needs_clarification=True,
            )

        # Create workout model
        workout = Workout(**workout_params)

        return ChatResponse(
            message=f"Зрозумів! Генерую плейлист на {workout.duration_minutes} хв...",
            workout=workout,
            needs_clarification=False,
        )

    except ValueError as e:
        logger.error(f"Workout parsing error: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to parse workout intent: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Unexpected error in chat endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while processing chat message",
        )

