"""
User preferences endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger

from app.services.supabase_service import SupabaseService
from app.schemas.user import (
    UserPreferencesResponse,
    UserPreferencesUpdateRequest,
    UserPreferences,
)

router = APIRouter(prefix="/users", tags=["users"])


def get_supabase_service() -> SupabaseService:
    """Dependency to get SupabaseService instance."""
    return SupabaseService()


@router.get("/{user_id}/preferences", response_model=UserPreferencesResponse)
async def get_user_preferences(
    user_id: str,
    supabase: SupabaseService = Depends(get_supabase_service),
) -> UserPreferencesResponse:
    """
    Get user preferences.

    Args:
        user_id: User ID
        supabase: SupabaseService dependency

    Returns:
        User preferences

    Raises:
        HTTPException: If user not found or retrieval fails
    """
    try:
        logger.info(f"Fetching preferences for user {user_id}")

        # Get user from database
        result = (
            supabase.get_client()
            .table("users")
            .select("id, preferences")
            .eq("id", user_id)
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="User not found")

        user = result.data[0]
        preferences_data = user.get("preferences") or {
            "top_genres": [],
            "top_artists": [],
            "avg_bpm": 145,
        }

        return UserPreferencesResponse(
            user_id=user["id"],
            preferences=UserPreferences(**preferences_data),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user preferences: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get user preferences: {str(e)}",
        )


@router.put("/{user_id}/preferences", response_model=UserPreferencesResponse)
async def update_user_preferences(
    user_id: str,
    request: UserPreferencesUpdateRequest,
    supabase: SupabaseService = Depends(get_supabase_service),
) -> UserPreferencesResponse:
    """
    Update user preferences.

    Args:
        user_id: User ID
        request: Updated preferences
        supabase: SupabaseService dependency

    Returns:
        Updated user preferences

    Raises:
        HTTPException: If user not found or update fails
    """
    try:
        logger.info(f"Updating preferences for user {user_id}")

        # Update user preferences
        result = (
            supabase.get_client()
            .table("users")
            .update(
                {
                    "preferences": request.preferences.model_dump(),
                    "updated_at": "now()",
                }
            )
            .eq("id", user_id)
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="User not found")

        user = result.data[0]
        preferences_data = user.get("preferences") or {
            "top_genres": [],
            "top_artists": [],
            "avg_bpm": 145,
        }

        return UserPreferencesResponse(
            user_id=user["id"],
            preferences=UserPreferences(**preferences_data),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update user preferences: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update user preferences: {str(e)}",
        )

