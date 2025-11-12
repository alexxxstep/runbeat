"""
Playlist generation endpoints.
"""
import time
from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from typing import List, Optional
from datetime import datetime

from app.services.spotify_service import SpotifyService
from app.services.playlist_generator import PlaylistGenerator
from app.services.supabase_service import SupabaseService
from app.schemas.playlist import PlaylistGenerateRequest, PlaylistGenerateResponse

router = APIRouter(prefix="/playlists", tags=["playlists"])


def get_supabase_service() -> SupabaseService:
    """Dependency to get SupabaseService instance."""
    return SupabaseService()


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
        playlist_data = await generator.generate(
            workout=request.workout,
            user_preferences=request.user_preferences or {},
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
                    .select("spotify_user_id, spotify_access_token")
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
                    new_user = (
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

        # Get playlists from database
        result = (
            supabase.get_client()
            .table("playlists")
            .select("*", count="exact")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .offset(offset)
            .execute()
        )

        playlists = []
        for p in result.data:
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
                }
            )

        return {
            "playlists": playlists,
            "total": result.count if result.count is not None else len(playlists),
        }

    except Exception as e:
        logger.error(f"Failed to get playlist history: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get playlist history: {str(e)}",
        )
