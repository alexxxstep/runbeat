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

        response_message, created_workout = await supervisor_agent.handle_message(
            user_id=request.user_id, message=request.message
        )

        # Return workout object if created (for frontend to update history & show as active)
        from app.models.workout import Workout
        workout_obj = None
        if created_workout:
            try:
                workout_obj = Workout(**created_workout)
            except Exception as e:
                logger.error(f"Failed to convert workout dict to Workout model: {e}")

        return ChatResponse(
            message=response_message,
            workout=workout_obj,  # Include created workout for frontend
            playlist=None,
            needs_clarification=False,  # Agent manages the flow
            is_complete=bool(created_workout),  # Complete if workout was created
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))
