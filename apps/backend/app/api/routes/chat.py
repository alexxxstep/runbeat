"""
Chat API endpoints with conversation flow management.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from typing import Optional, Dict, Any

from app.services.llm_service import LLMService
from app.services.conversation_manager import (
    ConversationManager,
    ConversationStateEnum,
    ConversationAction,
)
from app.services.supabase_service import SupabaseService
from app.services.spotify_service import SpotifyService
from app.schemas.chat import ChatRequest, ChatResponse
from app.models.workout import Workout

router = APIRouter(prefix="/chat", tags=["chat"])


def get_llm_service() -> LLMService:
    """Get LLM service instance."""
    return LLMService()


def get_supabase_service() -> SupabaseService:
    """Get Supabase service instance."""
    return SupabaseService()


def get_spotify_service() -> SpotifyService:
    """Get Spotify service instance."""
    return SpotifyService()


def get_conversation_manager(
    llm_service: LLMService = Depends(get_llm_service),
    spotify_service: SpotifyService = Depends(get_spotify_service),
) -> ConversationManager:
    """Get conversation manager instance."""
    return ConversationManager(llm_service=llm_service, spotify_service=spotify_service)


async def get_user_preferences_from_db(
    user_id: str,
    supabase: SupabaseService,
) -> Optional[Dict[str, Any]]:
    """
    Get user preferences from database.

    Args:
        user_id: User ID
        supabase: SupabaseService instance

    Returns:
        User preferences dictionary or None if not found/error
    """
    try:
        result = (
            supabase.get_client()
            .table("users")
            .select("preferences")
            .eq("id", user_id)
            .execute()
        )

        if result.data and len(result.data) > 0:
            preferences = result.data[0].get("preferences")
            if preferences:
                # Convert to format expected by ConversationManager
                return {
                    "favorite_genres": preferences.get("top_genres", []),
                    "top_genres": preferences.get("top_genres", []),
                    "top_artists": preferences.get("top_artists", []),
                    "avg_bpm": preferences.get("avg_bpm", 145),
                }
        return None
    except Exception as e:
        logger.warning(f"Failed to fetch user preferences for {user_id}: {e}")
        return None


@router.post("/message", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    conversation_manager: ConversationManager = Depends(get_conversation_manager),
    supabase: SupabaseService = Depends(get_supabase_service),
) -> ChatResponse:
    """
    Process chat message with conversation flow management.

    Handles:
    - Multi-turn conversations
    - Context preservation
    - Intelligent follow-ups
    - Playlist generation when ready

    Returns:
        Response with next action and data
    """
    try:
        # Validate user_id is provided for conversation management
        if not request.user_id:
            raise HTTPException(
                status_code=400,
                detail="user_id is required for conversation management",
            )

        # Get user_preferences from database
        user_preferences = await get_user_preferences_from_db(
            user_id=request.user_id, supabase=supabase
        )

        # Process message through conversation manager
        conversation_id, response_data = await conversation_manager.process_message(
            user_id=request.user_id,
            message=request.message,
            conversation_id=request.conversation_id,
            user_preferences=user_preferences,
        )

        # Convert workout_intent to Workout model if available
        workout = None
        if response_data.get("workout_intent"):
            from app.schemas.llm_responses import WorkoutIntent

            intent_dict = response_data["workout_intent"]
            workout_intent = WorkoutIntent(**intent_dict)
            workout = workout_intent.to_workout()

        # Determine needs_clarification and is_complete from state
        state = response_data.get("state", ConversationStateEnum.NEEDS_CLARIFICATION)
        needs_clarification = state == ConversationStateEnum.NEEDS_CLARIFICATION
        is_complete = state == ConversationStateEnum.COMPLETE

        # Get playlist if available (when conversation is complete)
        playlist = response_data.get("playlist")

        return ChatResponse(
            message=response_data.get("message_to_user", ""),
            workout=workout,
            playlist=playlist,
            needs_clarification=needs_clarification,
            conversation_id=conversation_id,
            is_complete=is_complete,
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Workout parsing error: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to parse workout intent: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversation/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    user_id: str = Query(..., description="User ID (for authorization)"),
    conversation_manager: ConversationManager = Depends(get_conversation_manager),
) -> Dict[str, Any]:
    """
    Get conversation by ID.

    Args:
        conversation_id: Conversation identifier
        user_id: User ID (for authorization)

    Returns:
        Complete conversation data

    Raises:
        HTTPException: If conversation not found
    """
    # Try to load from database if not in memory
    conversation = conversation_manager.get_conversation(conversation_id)
    if not conversation:
        conversation = await conversation_manager._load_conversation(
            conversation_id, user_id
        )

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Verify user owns this conversation
    if conversation.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    return conversation


@router.delete("/conversation/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    user_id: str = Query(..., description="User ID (for authorization)"),
    conversation_manager: ConversationManager = Depends(get_conversation_manager),
) -> Dict[str, str]:
    """
    Delete conversation.

    Args:
        conversation_id: Conversation identifier
        user_id: User ID (for authorization)

    Returns:
        Success message

    Raises:
        HTTPException: If conversation not found
    """
    # Load conversation to verify ownership
    conversation = conversation_manager.get_conversation(conversation_id)
    if not conversation:
        conversation = await conversation_manager._load_conversation(
            conversation_id, user_id
        )

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Verify user owns this conversation
    if conversation.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Remove from memory
    if conversation_id in conversation_manager.conversations:
        del conversation_manager.conversations[conversation_id]

    # Delete from database
    try:
        from app.services.supabase_service import supabase_service

        supabase_service.get_client().table("conversations").delete().eq(
            "id", conversation_id
        ).eq("user_id", user_id).execute()
    except Exception as e:
        logger.error(f"Error deleting conversation from database: {e}")

    return {"message": "Conversation deleted"}

