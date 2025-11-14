"""
Database tools for LangChain agents.
"""
from typing import List, Dict, Optional
from langchain.tools import tool
from loguru import logger

from app.services.supabase_service import supabase_service


@tool
def get_user_preferences(user_id: str) -> str:
    """
    Get user's music and workout preferences from database.

    Args:
        user_id: User ID

    Returns:
        JSON string with user preferences:
        - favorite_genres: List of favorite genres
        - top_artists: List of top artists
        - workout_history: List of previous workouts
        - music_history: List of previous playlists
    """
    try:
        import json

        client = supabase_service.get_client()

        # Get user data
        user_data = (
            client.table("users")
            .select("*")
            .eq("id", user_id)
            .execute()
        )

        if not user_data.data:
            return json.dumps({})

        user = user_data.data[0]

        # Get workout history
        workouts = (
            client.table("workouts")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(10)
            .execute()
        )

        # Get playlist history
        playlists = (
            client.table("playlists")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(10)
            .execute()
        )

        preferences = {
            "favorite_genres": user.get("favorite_genres", []),
            "top_artists": user.get("top_artists", []),
            "workout_history": workouts.data or [],
            "music_history": playlists.data or [],
        }

        logger.debug(f"Retrieved preferences for user {user_id}")
        return json.dumps(preferences, default=str)

    except Exception as e:
        logger.error(f"Error getting user preferences: {e}")
        return json.dumps({})


@tool
def get_user_music_history(user_id: str) -> str:
    """
    Get user's music/playlist history.

    Args:
        user_id: User ID

    Returns:
        JSON string with list of previous playlists
    """
    try:
        import json

        client = supabase_service.get_client()

        playlists = (
            client.table("playlists")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(20)
            .execute()
        )

        logger.debug(f"Retrieved {len(playlists.data or [])} playlists for user {user_id}")
        return json.dumps(playlists.data or [], default=str)

    except Exception as e:
        logger.error(f"Error getting music history: {e}")
        return json.dumps([])


@tool
def save_conversation(conversation_id: str, messages: List[Dict]) -> str:
    """
    Save conversation to database.

    Args:
        conversation_id: Conversation ID
        messages: List of messages (with role and content)

    Returns:
        "success" if saved, "error" if failed
    """
    try:
        client = supabase_service.get_client()

        # Extract user_id from first user message
        user_id = None
        for msg in messages:
            if msg.get("role") == "user":
                # Try to get user_id from conversation or message
                break

        if not user_id:
            return "error: user_id not found"

        # Upsert conversation
        client.table("conversations").upsert({
            "id": conversation_id,
            "messages": messages,
            "updated_at": "now()",
        }).execute()

        logger.debug(f"Saved conversation {conversation_id}")
        return "success"

    except Exception as e:
        logger.error(f"Error saving conversation: {e}")
        return f"error: {str(e)}"


@tool
def get_conversation_history(conversation_id: str) -> str:
    """
    Get conversation history from database.

    Args:
        conversation_id: Conversation ID

    Returns:
        JSON string with conversation messages
    """
    try:
        import json

        client = supabase_service.get_client()

        conversation = (
            client.table("conversations")
            .select("*")
            .eq("id", conversation_id)
            .execute()
        )

        if not conversation.data:
            return json.dumps([])

        messages = conversation.data[0].get("messages", [])
        return json.dumps(messages)

    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        return json.dumps([])

