"""
Chat API endpoints with conversation flow management.
"""

from fastapi import APIRouter, HTTPException
from loguru import logger

from app.agents.supervisor import supervisor_agent
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/message", response_model=ChatResponse)
async def send_message(request: ChatRequest) -> ChatResponse:
    """
    Processes a chat message using the new conversational agent system.
    """
    try:
        if not request.user_id:
            raise HTTPException(
                status_code=400,
                detail="user_id is required for conversation management",
            )

        update = await supervisor_agent.handle_message(
            user_id=request.user_id, message=request.message
        )

        # Return workout object if created (for frontend to update history & show as active)
        from app.models.workout import Workout

        workout_obj = None
        if update.created_workout:
            try:
                # Validate that workout has required fields before converting
                if all(
                    key in update.created_workout for key in ["type", "duration_minutes", "intensity"]
                ):
                    workout_obj = Workout(**update.created_workout)
                else:
                    logger.warning(
                        f"Created workout missing required fields: {update.created_workout}"
                    )
            except Exception as e:
                logger.error(f"Failed to convert workout dict to Workout model: {e}")

        return ChatResponse(
            message=update.response_message,
            workout=workout_obj,  # Include created workout for frontend
            playlist=None,
            needs_clarification=update.needs_clarification,
            is_complete=update.is_complete or bool(workout_obj),
        )

    except HTTPException:
        raise
    except Exception as e:
        error_str = str(e).lower()
        error_repr = repr(e).lower()
        error_type = type(e).__name__

        logger.error(
            f"Error in chat endpoint: {e} " f"(type: {error_type}, str: {error_str[:200]})"
        )

        # Check if it's a validation error related to workout parameters
        # This might happen if error propagates from AgentExecutor
        # Only catch errors that specifically mention duration/intensity
        is_validation_error = (
            ("duration" in error_str and "intensity" in error_str)
            or ("duration" in error_repr and "intensity" in error_repr)
            or ("'duration'" in error_str and "'intensity'" in error_str)
            or (
                error_type == "ValidationError"
                and ("duration" in error_str or "intensity" in error_str)
            )
        )

        if is_validation_error:
            logger.warning(
                f"Validation error detected in chat endpoint - "
                f"likely from tool validation. Returning user-friendly error."
            )
            # Return a 200 response with error message instead of 500
            return ChatResponse(
                message=(
                    "Вибачте, мені потрібно спочатку зібрати всі параметри. "
                    "Повідомте тривалість та інтенсивність тренування."
                ),
                workout=None,
                playlist=None,
                needs_clarification=True,
                is_complete=False,
            )

        raise HTTPException(status_code=500, detail=str(e))
