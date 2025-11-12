"""
Spotify OAuth authentication endpoints.
"""
import secrets
import urllib.parse
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from loguru import logger
from datetime import datetime, timedelta

from app.core.config import settings
from app.services.supabase_service import SupabaseService
from app.services.spotify_service import SpotifyService
from app.schemas.auth import SpotifyAuthResponse, SpotifyCallbackResponse
import spotipy
from spotipy.oauth2 import SpotifyOAuth

router = APIRouter(prefix="/auth", tags=["auth"])

# In-memory state storage (in production, use Redis or database)
oauth_states = {}


def get_spotify_oauth() -> SpotifyOAuth:
    """Get Spotify OAuth manager."""
    return SpotifyOAuth(
        client_id=settings.SPOTIFY_CLIENT_ID,
        client_secret=settings.SPOTIFY_CLIENT_SECRET,
        redirect_uri=settings.SPOTIFY_REDIRECT_URI,
        scope="user-read-private user-read-email user-top-read playlist-modify-private playlist-modify-public",
        cache_path=None,  # We'll handle token storage in Supabase
    )


@router.get("/spotify", response_model=SpotifyAuthResponse)
async def spotify_auth(
    user_id: Optional[str] = Query(
        None, description="User ID (optional, for linking Spotify to existing user)"
    ),
):
    """
    Initiate Spotify OAuth flow.
    Returns authorization URL for user to visit.

    Args:
        user_id: Optional user ID to link Spotify account to existing user
    """
    try:
        # Generate state for CSRF protection
        state = secrets.token_urlsafe(32)
        oauth_states[state] = {
            "created_at": datetime.now(),
            "used": False,
        }

        # Store user_id in state if provided (for linking Spotify to Google Auth user)
        if user_id:
            oauth_states[state]["user_id"] = user_id
            logger.info(f"Storing user_id {user_id} in OAuth state")

        # Build authorization URL
        oauth = get_spotify_oauth()
        auth_url = oauth.get_authorize_url(state=state)

        logger.info(f"Spotify OAuth initiated with state: {state[:8]}...")

        return SpotifyAuthResponse(auth_url=auth_url, state=state)

    except Exception as e:
        logger.error(f"Failed to initiate Spotify OAuth: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initiate Spotify authentication: {str(e)}",
        )


@router.get("/spotify/callback")
async def spotify_callback(
    code: str = Query(..., description="Authorization code from Spotify"),
    state: str = Query(..., description="OAuth state for CSRF protection"),
    error: str = Query(None, description="Error from Spotify OAuth"),
):
    """
    Handle Spotify OAuth callback.
    Exchanges authorization code for access token and saves to database.
    """
    try:
        # Check for errors
        if error:
            logger.error(f"Spotify OAuth error: {error}")
            return RedirectResponse(
                url=f"{settings.CORS_ORIGINS[0]}/auth/error?error={urllib.parse.quote(error)}"
            )

        # Validate state
        if state not in oauth_states:
            logger.error(f"Invalid OAuth state: {state[:8]}...")
            return RedirectResponse(
                url=f"{settings.CORS_ORIGINS[0]}/auth/error?error=invalid_state"
            )

        state_data = oauth_states[state]
        if state_data["used"]:
            logger.error(f"OAuth state already used: {state[:8]}...")
            return RedirectResponse(
                url=f"{settings.CORS_ORIGINS[0]}/auth/error?error=state_already_used"
            )

        # Check state expiration (5 minutes)
        if datetime.now() - state_data["created_at"] > timedelta(minutes=5):
            logger.error(f"OAuth state expired: {state[:8]}...")
            del oauth_states[state]
            return RedirectResponse(
                url=f"{settings.CORS_ORIGINS[0]}/auth/error?error=state_expired"
            )

        # Mark state as used
        state_data["used"] = True

        # Exchange code for token
        oauth = get_spotify_oauth()
        token_info = oauth.get_access_token(code, as_dict=False)

        # Get user info from Spotify
        spotify = spotipy.Spotify(auth=token_info)
        user_info = spotify.current_user()

        spotify_user_id = user_info["id"]
        email = user_info.get("email") or f"{spotify_user_id}@spotify.local"

        # Save or update user in Supabase
        supabase = SupabaseService().get_client()

        # Try to get user_id from state (if provided during OAuth flow)
        # Otherwise, check if user exists by spotify_user_id
        user_id = None
        if state in oauth_states and "user_id" in oauth_states[state]:
            user_id = oauth_states[state]["user_id"]
            logger.info(
                f"Found user_id from OAuth state: {user_id}"
            )

        # Check if user exists by spotify_user_id or by user_id
        existing_user = None
        if user_id:
            existing_user = (
                supabase.table("users")
                .select("id, spotify_user_id")
                .eq("id", user_id)
                .execute()
            )

        if not existing_user or not existing_user.data:
            # Try to find by spotify_user_id
            existing_user = (
                supabase.table("users")
                .select("id, spotify_user_id")
                .eq("spotify_user_id", spotify_user_id)
                .execute()
            )

        expires_at = datetime.now() + \
            timedelta(seconds=token_info["expires_in"])

        if existing_user.data:
            # Update existing user
            user_id = existing_user.data[0]["id"]
            supabase.table("users").update(
                {
                    "spotify_user_id": spotify_user_id,
                    "spotify_access_token": token_info["access_token"],
                    "spotify_refresh_token": token_info.get("refresh_token"),
                    "spotify_token_expires_at": expires_at.isoformat(),
                    "updated_at": datetime.now().isoformat(),
                }
            ).eq("id", user_id).execute()

            logger.info(f"Updated user {user_id} with new Spotify token")
        else:
            # Create new user or update if user_id provided
            if user_id:
                # User exists in Supabase Auth but not in users table
                # Use upsert to create or update
                upsert_result = (
                    supabase.table("users")
                    .upsert(
                        {
                            "id": user_id,
                            "email": email,
                            "spotify_user_id": spotify_user_id,
                            "spotify_access_token": token_info["access_token"],
                            "spotify_refresh_token": token_info.get("refresh_token"),
                            "spotify_token_expires_at": expires_at.isoformat(),
                            "preferences": {
                                "top_genres": [],
                                "top_artists": [],
                                "avg_bpm": 145,
                            },
                        },
                        on_conflict="id",
                    )
                    .execute()
                )
                logger.info(
                    f"Upserted user {user_id} with Spotify connection"
                )
            else:
                # Create new user
                new_user = (
                    supabase.table("users")
                    .insert(
                        {
                            "email": email,
                            "spotify_user_id": spotify_user_id,
                            "spotify_access_token": token_info["access_token"],
                            "spotify_refresh_token": token_info.get("refresh_token"),
                            "spotify_token_expires_at": expires_at.isoformat(),
                            "preferences": {
                                "top_genres": [],
                                "top_artists": [],
                                "avg_bpm": 145,
                            },
                        }
                    )
                    .execute()
                )
                user_id = new_user.data[0]["id"]
                logger.info(
                    f"Created new user {user_id} with Spotify ID {spotify_user_id}"
                )

        # Clean up old states (keep last 100)
        if len(oauth_states) > 100:
            sorted_states = sorted(
                oauth_states.items(),
                key=lambda x: x[1]["created_at"],
                reverse=True,
            )
            for old_state, _ in sorted_states[100:]:
                del oauth_states[old_state]

        # Redirect to frontend with success
        return RedirectResponse(
            url=f"{settings.CORS_ORIGINS[0]}/auth/success?user_id={user_id}&spotify_user_id={spotify_user_id}"
        )

    except Exception as e:
        logger.error(f"Failed to handle Spotify callback: {e}")
        return RedirectResponse(
            url=f"{settings.CORS_ORIGINS[0]}/auth/error?error={urllib.parse.quote(str(e))}"
        )


@router.get("/spotify/status")
async def spotify_auth_status(user_id: str = Query(..., description="User ID")):
    """
    Check Spotify authentication status for a user.
    """
    try:
        supabase = SupabaseService().get_client()

        user = (
            supabase.table("users")
            .select("id, spotify_user_id, spotify_token_expires_at")
            .eq("id", user_id)
            .execute()
        )

        if not user.data:
            raise HTTPException(status_code=404, detail="User not found")

        user_data = user.data[0]
        expires_at = user_data.get("spotify_token_expires_at")

        if not expires_at:
            return {"authenticated": False, "message": "User not authenticated with Spotify"}

        # Check if token is expired
        expires_datetime = datetime.fromisoformat(
            expires_at.replace("Z", "+00:00"))
        is_expired = datetime.now(expires_datetime.tzinfo) >= expires_datetime

        return {
            "authenticated": not is_expired,
            "spotify_user_id": user_data.get("spotify_user_id"),
            "expires_at": expires_at,
            "is_expired": is_expired,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to check Spotify auth status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check authentication status: {str(e)}",
        )
