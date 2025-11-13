"""
Playlist generation endpoints.
"""
import time
import random
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger

from app.core.config import settings
from app.schemas.playlist import (
    PlaylistGenerateRequest,
    PlaylistGenerateResponse,
    PlaylistVariantsResponse,
    TrackVariant,
)
from app.services.playlist_generator import PlaylistGenerator
from app.services.spotify_service import SpotifyService
from app.services.supabase_service import SupabaseService

router = APIRouter(prefix="/playlists", tags=["playlists"])


# Singleton instance to avoid creating new clients on every request
_supabase_service_instance: Optional[SupabaseService] = None

def get_supabase_service() -> SupabaseService:
    """Dependency to get SupabaseService instance (singleton)."""
    global _supabase_service_instance
    if _supabase_service_instance is None:
        _supabase_service_instance = SupabaseService()
    return _supabase_service_instance


def get_spotify_service() -> SpotifyService:
    """Dependency to get SpotifyService instance."""
    return SpotifyService()


def get_playlist_generator(
    spotify: SpotifyService = Depends(get_spotify_service),
) -> PlaylistGenerator:
    """Dependency to get PlaylistGenerator instance."""
    return PlaylistGenerator(spotify)


@router.post("/generate", response_model=PlaylistGenerateResponse)
async def generate_playlist(
    request: PlaylistGenerateRequest,
    generator: PlaylistGenerator = Depends(get_playlist_generator),
    spotify_service: SpotifyService = Depends(get_spotify_service),
) -> PlaylistGenerateResponse:
    """
    Generate workout playlist based on workout parameters.

    Args:
        request: Playlist generation request with workout and preferences
        generator: PlaylistGenerator dependency

    Returns:
        PlaylistGenerateResponse with generated tracks

    Raises:
        HTTPException: If generation fails
    """
    start_time = time.time()

    try:
        logger.info(
            f"Generating playlist for {request.workout.type} workout, "
            f"{request.workout.duration_minutes} min"
        )

        # Generate playlist
        interval_stages = None
        if request.interval_stages:
            interval_stages = [
                {
                    "name": stage.name,
                    "duration_minutes": stage.duration_minutes,
                    "hr_zone": stage.hr_zone,
                    "bpm_range": stage.bpm_range,
                }
                for stage in request.interval_stages
            ]

        # Get user's Spotify token if available
        user_token = None
        if request.user_id:
            try:
                supabase = SupabaseService().get_client()
                user_data = (
                    supabase.table("users")
                    .select("spotify_access_token, spotify_token_expires_at")
                    .eq("id", request.user_id)
                    .execute()
                )

                if user_data.data and user_data.data[0].get("spotify_access_token"):
                    # Check if token is expired
                    expires_at_str = user_data.data[0].get("spotify_token_expires_at")
                    if expires_at_str:
                        from datetime import datetime
                        expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
                        if expires_at > datetime.now(expires_at.tzinfo):
                            user_token = user_data.data[0]["spotify_access_token"]
                            logger.debug(f"Using user token for playlist generation")
            except Exception as token_error:
                logger.warning(f"Failed to get user token: {token_error}, using Client Credentials")

        playlist_data = await generator.generate(
            workout=request.workout,
            user_preferences=request.user_preferences or {},
            interval_stages=interval_stages,
            prompt=request.prompt,
            user_token=user_token,
        )

        generation_time = time.time() - start_time

        logger.info(
            f"Playlist generated successfully: {playlist_data.total_tracks} tracks, "
            f"{generation_time:.2f}s"
        )

        # Convert tracks to dict for response
        tracks_dict = [track.model_dump() for track in playlist_data.tracks]

        playlist_id = None
        spotify_url = None

        # If user_id provided, try to create playlist in Spotify
        if request.user_id and playlist_data.tracks:
            try:
                logger.info(
                    f"Creating Spotify playlist for user {request.user_id}")

                # Get user's Spotify token from database
                supabase = SupabaseService().get_client()
                user_data = (
                    supabase.table("users")
                    .select(
                        "spotify_user_id, spotify_access_token, "
                        "spotify_refresh_token, spotify_token_expires_at"
                    )
                    .eq("id", request.user_id)
                    .execute()
                )

                # If user doesn't exist in users table, create entry
                # (for users who signed in with Google but haven't connected Spotify)
                if not user_data.data:
                    logger.info(
                        f"User {request.user_id} not found in users table, "
                        "creating entry"
                    )
                    # Get user email from Supabase Auth (if available)
                    # For now, create minimal entry
                    (
                        supabase.table("users")
                        .insert(
                            {
                                "id": request.user_id,
                                "email": None,  # Will be updated when Spotify connected
                                "preferences": {
                                    "top_genres": [],
                                    "top_artists": [],
                                    "avg_bpm": 145,
                                },
                            }
                        )
                        .execute()
                    )
                    logger.info(f"Created user entry for {request.user_id}")
                    # User doesn't have Spotify connected yet
                    user_data = {"data": [{}]}

                if user_data.data and user_data.data[0].get("spotify_access_token"):
                    spotify_user_id = user_data.data[0]["spotify_user_id"]
                    access_token = user_data.data[0]["spotify_access_token"]
                    refresh_token = user_data.data[0].get(
                        "spotify_refresh_token")
                    expires_at_str = user_data.data[0].get(
                        "spotify_token_expires_at"
                    )

                    # Check if token is expired and refresh if needed
                    if expires_at_str:
                        try:
                            expires_at = datetime.fromisoformat(
                                expires_at_str.replace("Z", "+00:00")
                            )
                            # Refresh if expires in less than 5 minutes
                            if datetime.now(expires_at.tzinfo) >= (
                                expires_at - timedelta(minutes=5)
                            ):
                                if refresh_token:
                                    logger.info(
                                        f"Refreshing expired token for user "
                                        f"{request.user_id}"
                                    )
                                    # Refresh token using SpotifyOAuth
                                    from spotipy.oauth2 import SpotifyOAuth

                                    oauth = SpotifyOAuth(
                                        client_id=settings.SPOTIFY_CLIENT_ID,
                                        client_secret=settings.SPOTIFY_CLIENT_SECRET,
                                        redirect_uri=settings.SPOTIFY_REDIRECT_URI,
                                    )
                                    token_info = oauth.refresh_access_token(
                                        refresh_token
                                    )

                                    # Update token in database
                                    new_expires_at = datetime.now() + timedelta(
                                        seconds=token_info.get(
                                            "expires_in", 3600)
                                    )
                                    supabase.table("users").update(
                                        {
                                            "spotify_access_token": token_info[
                                                "access_token"
                                            ],
                                            "spotify_refresh_token": token_info.get(
                                                "refresh_token", refresh_token
                                            ),
                                            "spotify_token_expires_at": (
                                                new_expires_at.isoformat()
                                            ),
                                            "updated_at": datetime.now().isoformat(),
                                        }
                                    ).eq("id", request.user_id).execute()

                                    access_token = token_info["access_token"]
                                    logger.info("Token refreshed successfully")
                                else:
                                    logger.warning(
                                        f"No refresh token for user {request.user_id}"
                                    )
                        except Exception as token_error:
                            logger.warning(
                                f"Failed to check/refresh token: {token_error}. "
                                "Trying with current token"
                            )

                    # Create Spotify client with user token
                    user_client = spotify_service.get_user_client(access_token)

                    # Generate playlist name
                    workout_type_map = {
                        "steady": "Стабільна",
                        "progressive": "Прогресивна",
                        "intervals": "Інтервальна",
                        "fartlek": "Фартлек",
                    }
                    workout_name = workout_type_map.get(
                        request.workout.type, "Тренування"
                    )
                    playlist_name = (
                        f"RunBeat: {workout_name} пробіжка "
                        f"({request.workout.duration_minutes} хв)"
                    )

                    # Get track URIs
                    track_uris = [
                        track.spotify_uri
                        for track in playlist_data.tracks
                        if track.spotify_uri
                    ]

                    if track_uris:
                        # Create playlist in Spotify
                        playlist_info = await spotify_service.create_playlist(
                            user_client=user_client,
                            user_id=spotify_user_id,
                            name=playlist_name,
                            tracks=track_uris,
                            description=(
                                f"AI-згенерований плейлист для "
                                f"{workout_name.lower()} тренування. "
                                f"Тривалість: {request.workout.duration_minutes} хв. "
                                f"Інтенсивність: {request.workout.intensity}."
                            ),
                        )

                        playlist_id = playlist_info["id"]
                        spotify_url = playlist_info["url"]

                        logger.info(
                            f"Playlist created in Spotify: {spotify_url}"
                        )

                        # Save playlist to database
                        try:
                            # First, create or get workout record
                            workout_result = (
                                supabase.table("workouts")
                                .insert(
                                    {
                                        "user_id": request.user_id,
                                        "type": request.workout.type,
                                        "duration_minutes": (
                                            request.workout.duration_minutes
                                        ),
                                        "intensity": request.workout.intensity,
                                        "hr_zones": request.workout.hr_zones,
                                    }
                                )
                                .execute()
                            )
                            workout_db_id = workout_result.data[0]["id"]

                            # Save playlist to database
                            playlist_db_result = (
                                supabase.table("playlists")
                                .insert(
                                    {
                                        "user_id": request.user_id,
                                        "workout_id": workout_db_id,
                                        "spotify_playlist_id": playlist_id,
                                        "spotify_url": spotify_url,
                                        "tracks": tracks_dict,
                                        "total_duration_seconds": int(
                                            playlist_data.total_duration
                                        ),
                                        "generation_time_seconds": (
                                            generation_time
                                        ),
                                    }
                                )
                                .execute()
                            )
                            logger.info(
                                f"Playlist saved to database: "
                                f"{playlist_db_result.data[0]['id']}"
                            )
                        except Exception as db_error:
                            logger.error(
                                f"Failed to save playlist to database: "
                                f"{db_error}"
                            )
                            # Continue - playlist is created in Spotify anyway
                    else:
                        logger.warning(
                            "No track URIs available to create playlist"
                        )
                else:
                    logger.warning(
                        f"User {request.user_id} not found or "
                        "not authenticated with Spotify"
                    )
            except Exception as create_error:
                logger.error(
                    f"Failed to create Spotify playlist: {create_error}"
                )
                # Continue without playlist - return tracks anyway

        return PlaylistGenerateResponse(
            playlist_id=playlist_id,
            spotify_url=spotify_url,
            tracks=tracks_dict,
            total_duration=playlist_data.total_duration,
            total_tracks=playlist_data.total_tracks,
            generation_time_seconds=round(generation_time, 2),
        )

    except Exception as e:
        logger.error(f"Failed to generate playlist: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate playlist: {str(e)}",
        )


@router.get("/history")
async def get_playlist_history(
    user_id: str = Query(..., description="User ID"),
    limit: int = Query(
        10, ge=1, le=100, description="Number of playlists to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    supabase: SupabaseService = Depends(get_supabase_service),
) -> dict:
    """
    Get playlist history for a user.

    Args:
        user_id: User ID
        limit: Maximum number of playlists to return
        offset: Pagination offset
        supabase: SupabaseService dependency

    Returns:
        List of playlists with metadata

    Raises:
        HTTPException: If retrieval fails
    """
    try:
        logger.info(f"Fetching playlist history for user {user_id}")

        # Get playlists from database with workout information
        result = (
            supabase.get_client()
            .table("playlists")
            .select("*, workouts(id, type, duration_minutes, intensity, hr_zones)")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .offset(offset)
            .execute()
        )

        playlists = []
        for p in result.data:
            # Handle workout data - Supabase returns it as a list or dict depending on relationship
            workout_data = p.get("workouts")
            workout = None
            if workout_data:
                if isinstance(workout_data, list):
                    # If it's a list, take the first item
                    workout = workout_data[0] if len(workout_data) > 0 else None
                elif isinstance(workout_data, dict):
                    # If it's already a dict, use it directly
                    workout = workout_data
                # Only include if workout has required fields
                if workout and workout.get("id") and workout.get("type"):
                    workout = {
                        "id": workout["id"],
                        "type": workout["type"],
                        "duration_minutes": workout.get("duration_minutes", 0),
                        "intensity": workout.get("intensity", "moderate"),
                        "hr_zones": workout.get("hr_zones", [110, 180]),
                    }
                else:
                    workout = None

            playlists.append(
                {
                    "id": p["id"],
                    "workout_id": p.get("workout_id"),
                    "spotify_playlist_id": p["spotify_playlist_id"],
                    "spotify_url": p["spotify_url"],
                    "total_tracks": len(p.get("tracks", [])),
                    "total_duration_seconds": p["total_duration_seconds"],
                    "generation_time_seconds": p["generation_time_seconds"],
                    "shared": p.get("shared", False),
                    "share_url": p.get("share_url"),
                    "created_at": p["created_at"],
                    "workout": workout,
                }
            )

        return {
            "playlists": playlists,
            "total": len(playlists),
        }

    except Exception as e:
        logger.error(f"Failed to get playlist history: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get playlist history: {str(e)}",
        )


@router.delete("/{playlist_id}")
async def delete_playlist(
    playlist_id: str,
    user_id: str = Query(..., description="User ID"),
    supabase: SupabaseService = Depends(get_supabase_service),
) -> dict:
    """
    Delete a playlist from database.

    Args:
        playlist_id: Playlist ID (database ID, not Spotify ID)
        user_id: User ID
        supabase: SupabaseService dependency

    Returns:
        Success message

    Raises:
        HTTPException: If deletion fails or playlist not found
    """
    try:
        logger.info(
            f"Deleting playlist {playlist_id} for user {user_id}"
        )

        # Check if playlist exists and belongs to user
        playlist_result = (
            supabase.get_client()
            .table("playlists")
            .select("id, user_id")
            .eq("id", playlist_id)
            .eq("user_id", user_id)
            .execute()
        )

        if not playlist_result.data:
            raise HTTPException(
                status_code=404,
                detail="Playlist not found or access denied"
            )

        # Delete playlist from database
        (
            supabase.get_client()
            .table("playlists")
            .delete()
            .eq("id", playlist_id)
            .eq("user_id", user_id)
            .execute()
        )

        logger.info(f"Playlist {playlist_id} deleted successfully")

        return {
            "success": True,
            "message": "Playlist deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete playlist: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete playlist: {str(e)}",
        )


@router.post("/preview-variants", response_model=PlaylistVariantsResponse)
async def preview_playlist_variants(
    request: PlaylistGenerateRequest,
    generator: PlaylistGenerator = Depends(get_playlist_generator),
) -> PlaylistVariantsResponse:
    """
    Generate 2 track variants for preview (without creating Spotify playlist).

    Args:
        request: Playlist generation request with workout and preferences
        generator: PlaylistGenerator dependency

    Returns:
        PlaylistVariantsResponse with 2 track variants

    Raises:
        HTTPException: If generation fails
    """
    start_time = time.time()

    try:
        logger.info(
            f"Generating 2 variants for {request.workout.type} workout, "
            f"{request.workout.duration_minutes} min"
        )

        # Prepare interval stages
        interval_stages = None
        if request.interval_stages:
            interval_stages = [
                {
                    "name": stage.name,
                    "duration_minutes": stage.duration_minutes,
                    "hr_zone": stage.hr_zone,
                    "bpm_range": stage.bpm_range,
                }
                for stage in request.interval_stages
            ]

        # Generate first variant with original preferences
        user_prefs_variant1 = request.user_preferences or {}
        try:
            # Get user token for variants generation
            user_token = None
            if request.user_id:
                try:
                    supabase = SupabaseService().get_client()
                    user_data = (
                        supabase.table("users")
                        .select("spotify_access_token, spotify_token_expires_at")
                        .eq("id", request.user_id)
                        .execute()
                    )

                    if user_data.data and user_data.data[0].get("spotify_access_token"):
                        expires_at_str = user_data.data[0].get("spotify_token_expires_at")
                        if expires_at_str:
                            expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
                            if expires_at > datetime.now(expires_at.tzinfo):
                                user_token = user_data.data[0]["spotify_access_token"]
                except Exception as token_error:
                    logger.warning(f"Failed to get user token: {token_error}")

            playlist_data_variant1 = await generator.generate(
                workout=request.workout,
                user_preferences=user_prefs_variant1,
                interval_stages=interval_stages,
                prompt=request.prompt,
                user_token=user_token,
            )
        except Exception as e:
            logger.error(f"Failed to generate variant 1: {e}", exc_info=True)
            raise

        # Generate second variant with slightly different preferences
        # AND exclude tracks from variant 1 to ensure different tracks
        user_prefs_variant2 = user_prefs_variant1.copy()
        # Add some variation - could be different genre emphasis or BPM adjustment
        if "top_genres" in user_prefs_variant2 and user_prefs_variant2["top_genres"]:
            # Shuffle genres for variety
            genres = user_prefs_variant2["top_genres"].copy()
            random.shuffle(genres)
            user_prefs_variant2["top_genres"] = genres
        elif "avg_bpm" in user_prefs_variant2:
            # Slight BPM variation (±5)
            user_prefs_variant2["avg_bpm"] = user_prefs_variant2.get(
                "avg_bpm", 145) + random.choice([-5, 5])

        # Exclude tracks from variant 1 to ensure different tracks in variant 2
        excluded_track_ids = [track.id for track in playlist_data_variant1.tracks]
        logger.info(f"Excluding {len(excluded_track_ids)} tracks from variant 1 when generating variant 2")

        try:
            playlist_data_variant2 = await generator.generate(
                workout=request.workout,
                user_preferences=user_prefs_variant2,
                interval_stages=interval_stages,
                prompt=request.prompt,
                user_token=user_token,
                excluded_track_ids=excluded_track_ids if excluded_track_ids else None,
            )
        except Exception as e:
            logger.error(f"Failed to generate variant 2: {e}", exc_info=True)
            raise

        generation_time = time.time() - start_time

        logger.info(
            f"Variants generated: "
            f"Variant 1: {playlist_data_variant1.total_tracks} tracks, "
            f"Variant 2: {playlist_data_variant2.total_tracks} tracks, "
            f"{generation_time:.2f}s"
        )

        # Validate that variants are not empty
        if playlist_data_variant1.total_tracks == 0 and playlist_data_variant2.total_tracks == 0:
            error_msg = (
                "Не вдалося знайти треки для воркауту. "
                "Можливі причини: некоректні параметри, проблеми з Spotify API, "
                "або відсутність жанрів музики. Спробуйте змінити параметри воркауту."
            )
            logger.error(error_msg)
            raise HTTPException(
                status_code=422,
                detail=error_msg
            )

        if playlist_data_variant1.total_tracks == 0:
            logger.warning("Variant 1 is empty, but variant 2 has tracks")
        if playlist_data_variant2.total_tracks == 0:
            logger.warning("Variant 2 is empty, but variant 1 has tracks")

        # Convert tracks to dict for response
        tracks_variant1 = [track.model_dump()
                           for track in playlist_data_variant1.tracks]
        tracks_variant2 = [track.model_dump()
                           for track in playlist_data_variant2.tracks]

        return PlaylistVariantsResponse(
            variant1=TrackVariant(
                tracks=tracks_variant1,
                total_duration=playlist_data_variant1.total_duration,
                total_tracks=playlist_data_variant1.total_tracks,
            ),
            variant2=TrackVariant(
                tracks=tracks_variant2,
                total_duration=playlist_data_variant2.total_duration,
                total_tracks=playlist_data_variant2.total_tracks,
            ),
            generation_time_seconds=generation_time,
        )

    except HTTPException:
        # Re-raise HTTP exceptions (like 422 for empty variants)
        raise
    except Exception as e:
        logger.error(f"Failed to generate playlist variants: {e}", exc_info=True)
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Full traceback: {error_details}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate playlist variants: {str(e)}",
        )
