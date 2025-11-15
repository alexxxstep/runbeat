"""
Chat API endpoints with conversation flow management.
"""
from fastapi import APIRouter, HTTPException
from loguru import logger
from app.schemas.chat import ChatRequest, ChatResponse
from app.agents.supervisor import supervisor_agent

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

        response_message = await supervisor_agent.handle_message(
            user_id=request.user_id, message=request.message
        )

        # The new system is simpler: the supervisor's response is the message.
        # The frontend will handle displaying workout info embedded in messages.
        return ChatResponse(
            message=response_message,
            workout=None,  # This will be handled via message content
            playlist=None,  # This will be handled via message content
            needs_clarification=False,  # The agent manages the flow
            is_complete=False,  # The agent manages the flow
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))
