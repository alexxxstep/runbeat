"""
Spotify API endpoints.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger

from app.schemas.spotify import (
    RecommendationRequest,
    RecommendationResponse,
    RecommendationTrack,
)
from app.services.spotify_service import SpotifyService

router = APIRouter(prefix="/spotify", tags=["spotify"])


def get_spotify_service() -> SpotifyService:
    """Dependency to get SpotifyService instance."""
    return SpotifyService()


def _trim_seeds(
    seed_artists: Optional[List[str]],
    seed_tracks: Optional[List[str]],
    seed_genres: Optional[List[str]],
) -> tuple:
    """
    Trim seeds to max 5 total.

    Args:
        seed_artists: List of artist IDs
        seed_tracks: List of track IDs
        seed_genres: List of genres

    Returns:
        Tuple of (trimmed_artists, trimmed_tracks, trimmed_genres)
    """
    seed_artists_list = list(seed_artists) if seed_artists else []
    seed_tracks_list = list(seed_tracks) if seed_tracks else []
    seed_genres_list = list(seed_genres) if seed_genres else []

    total_seeds = (
        len(seed_artists_list) +
        len(seed_tracks_list) +
        len(seed_genres_list)
    )

    if total_seeds > 5:
        logger.warning(
            f"Too many seeds ({total_seeds}), trimming to 5"
        )
        # Trim proportionally
        while total_seeds > 5:
            if seed_artists_list:
                seed_artists_list.pop()
                total_seeds -= 1
            if total_seeds > 5 and seed_tracks_list:
                seed_tracks_list.pop()
                total_seeds -= 1
            if total_seeds > 5 and seed_genres_list:
                seed_genres_list.pop()
                total_seeds -= 1

    return seed_artists_list, seed_tracks_list, seed_genres_list


def _convert_track_to_response(
    track: dict,
    phase: Optional[str] = None,
) -> RecommendationTrack:
    """
    Convert Spotify track dict to RecommendationTrack.

    Args:
        track: Spotify track dictionary
        phase: Optional workout phase

    Returns:
        RecommendationTrack instance
    """
    artists = [artist["name"] for artist in track.get("artists", [])]

    return RecommendationTrack(
        id=track.get("id", ""),
        name=track.get("name", "Unknown"),
        artists=artists,
        tempo=track.get("tempo"),
        energy=track.get("energy"),
        danceability=track.get("danceability"),
        duration_ms=track.get("duration_ms", 0),
        popularity=track.get("popularity"),
        uri=track.get("uri", ""),
        preview_url=track.get("preview_url"),
        phase=phase,
        seed_type="recommendation",
        seed_name="Spotify Recommendations",
    )


async def _get_recommendations_internal(
    request: RecommendationRequest,
    spotify_service: SpotifyService,
) -> RecommendationResponse:
    """
    Internal function to get recommendations.

    Args:
        request: Recommendation request
        spotify_service: SpotifyService instance

    Returns:
        RecommendationResponse

    Raises:
        ValueError: If no seeds provided
        Exception: If Spotify API call fails
    """
    try:
        # Validate seeds
        has_seeds = (
            (request.seed_artists and len(request.seed_artists) > 0) or
            (request.seed_tracks and len(request.seed_tracks) > 0) or
            (request.seed_genres and len(request.seed_genres) > 0)
        )

        if not has_seeds:
            return RecommendationResponse(
                status="error",
                count=0,
                recommendations=[],
                message="At least one of seed_artists, seed_tracks, "
                        "or seed_genres must be provided",
            )

        # Trim seeds if needed
        seed_artists_list, seed_tracks_list, seed_genres_list = _trim_seeds(
            request.seed_artists,
            request.seed_tracks,
            request.seed_genres,
        )

        # Get recommendations from Spotify
        tracks = await spotify_service.get_recommendations_advanced(
            seed_artists=seed_artists_list if seed_artists_list else None,
            seed_tracks=seed_tracks_list if seed_tracks_list else None,
            seed_genres=seed_genres_list if seed_genres_list else None,
            limit=request.limit,
            market=request.market,
            min_energy=request.min_energy,
            max_energy=request.max_energy,
            target_energy=request.target_energy,
            min_tempo=request.min_tempo,
            max_tempo=request.max_tempo,
            target_tempo=request.target_tempo,
            min_danceability=request.min_danceability,
            max_danceability=request.max_danceability,
            min_valence=request.min_valence,
            max_valence=request.max_valence,
            min_acousticness=request.min_acousticness,
            max_acousticness=request.max_acousticness,
        )

        # Convert tracks to response format
        recommendation_tracks = [
            _convert_track_to_response(track, request.phase)
            for track in tracks
        ]

        logger.info(
            f"Successfully retrieved {len(recommendation_tracks)} "
            f"recommendations"
        )

        return RecommendationResponse(
            status="success",
            count=len(recommendation_tracks),
            recommendations=recommendation_tracks,
            message=None,
        )

    except ValueError as e:
        logger.warning(f"Invalid request: {e}")
        return RecommendationResponse(
            status="error",
            count=0,
            recommendations=[],
            message=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to get recommendations: {e}")
        import traceback
        logger.debug(f"Traceback: {traceback.format_exc()}")
        return RecommendationResponse(
            status="error",
            count=0,
            recommendations=[],
            message=f"Failed to get recommendations: {str(e)}",
        )


@router.post(
    "/recommendations",
    response_model=RecommendationResponse,
    summary="Get Spotify recommendations",
    description=(
        "Get track recommendations from Spotify based on seeds "
        "(artists, tracks, or genres) and filters."
    ),
)
async def get_recommendations_post(
    request: RecommendationRequest,
    spotify_service: SpotifyService = Depends(get_spotify_service),
) -> RecommendationResponse:
    """
    Get Spotify track recommendations (POST method).

    Args:
        request: Recommendation request with seeds and filters
        spotify_service: SpotifyService dependency

    Returns:
        RecommendationResponse with recommended tracks

    Raises:
        HTTPException: If request validation fails
    """
    logger.info(
        f"POST /recommendations - seeds: artists={request.seed_artists}, "
        f"tracks={request.seed_tracks}, genres={request.seed_genres}, "
        f"limit={request.limit}"
    )

    try:
        return await _get_recommendations_internal(
            request, spotify_service
        )
    except Exception as e:
        logger.error(f"Unexpected error in POST /recommendations: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get(
    "/recommendations",
    response_model=RecommendationResponse,
    summary="Get Spotify recommendations",
    description=(
        "Get track recommendations from Spotify based on seeds "
        "(artists, tracks, or genres) and filters (GET method)."
    ),
)
async def get_recommendations_get(
    seed_artists: Optional[str] = Query(
        None,
        description="Comma-separated list of Spotify artist IDs (max 5)"
    ),
    seed_tracks: Optional[str] = Query(
        None,
        description="Comma-separated list of Spotify track IDs (max 5)"
    ),
    seed_genres: Optional[str] = Query(
        None,
        description="Comma-separated list of seed genres (max 5)"
    ),
    limit: int = Query(
        20,
        ge=1,
        le=100,
        description="Number of recommendations (1-100, default 20)"
    ),
    market: str = Query(
        "US",
        description="ISO country code (default 'US')"
    ),
    min_energy: Optional[float] = Query(
        None,
        ge=0.0,
        le=1.0,
        description="Minimum energy (0-1)"
    ),
    max_energy: Optional[float] = Query(
        None,
        ge=0.0,
        le=1.0,
        description="Maximum energy (0-1)"
    ),
    target_energy: Optional[float] = Query(
        None,
        ge=0.0,
        le=1.0,
        description="Target energy (0-1)"
    ),
    min_tempo: Optional[float] = Query(
        None,
        ge=0.0,
        le=250.0,
        description="Minimum tempo/BPM (0-250)"
    ),
    max_tempo: Optional[float] = Query(
        None,
        ge=0.0,
        le=250.0,
        description="Maximum tempo/BPM (0-250)"
    ),
    target_tempo: Optional[float] = Query(
        None,
        ge=0.0,
        le=250.0,
        description="Target tempo/BPM (0-250)"
    ),
    min_danceability: Optional[float] = Query(
        None,
        ge=0.0,
        le=1.0,
        description="Minimum danceability (0-1)"
    ),
    max_danceability: Optional[float] = Query(
        None,
        ge=0.0,
        le=1.0,
        description="Maximum danceability (0-1)"
    ),
    min_valence: Optional[float] = Query(
        None,
        ge=0.0,
        le=1.0,
        description="Minimum valence (0-1)"
    ),
    max_valence: Optional[float] = Query(
        None,
        ge=0.0,
        le=1.0,
        description="Maximum valence (0-1)"
    ),
    min_acousticness: Optional[float] = Query(
        None,
        ge=0.0,
        le=1.0,
        description="Minimum acousticness (0-1)"
    ),
    max_acousticness: Optional[float] = Query(
        None,
        ge=0.0,
        le=1.0,
        description="Maximum acousticness (0-1)"
    ),
    phase: Optional[str] = Query(
        None,
        description="Workout phase: 'warm-up', 'main', or 'cool-down'"
    ),
    spotify_service: SpotifyService = Depends(get_spotify_service),
) -> RecommendationResponse:
    """
    Get Spotify track recommendations (GET method).

    Args:
        seed_artists: Comma-separated list of artist IDs
        seed_tracks: Comma-separated list of track IDs
        seed_genres: Comma-separated list of genres
        limit: Number of recommendations
        market: ISO country code
        min_energy: Minimum energy
        max_energy: Maximum energy
        target_energy: Target energy
        min_tempo: Minimum tempo/BPM
        max_tempo: Maximum tempo/BPM
        target_tempo: Target tempo/BPM
        min_danceability: Minimum danceability
        max_danceability: Maximum danceability
        min_valence: Minimum valence
        max_valence: Maximum valence
        min_acousticness: Minimum acousticness
        max_acousticness: Maximum acousticness
        phase: Workout phase
        spotify_service: SpotifyService dependency

    Returns:
        RecommendationResponse with recommended tracks

    Raises:
        HTTPException: If request validation fails
    """
    # Parse comma-separated strings into lists
    seed_artists_list = (
        [s.strip() for s in seed_artists.split(",") if s.strip()]
        if seed_artists else None
    )
    seed_tracks_list = (
        [s.strip() for s in seed_tracks.split(",") if s.strip()]
        if seed_tracks else None
    )
    seed_genres_list = (
        [s.strip() for s in seed_genres.split(",") if s.strip()]
        if seed_genres else None
    )

    logger.info(
        f"GET /recommendations - seeds: artists={seed_artists_list}, "
        f"tracks={seed_tracks_list}, genres={seed_genres_list}, "
        f"limit={limit}"
    )

    # Validate phase
    if phase is not None and phase not in ["warm-up", "main", "cool-down"]:
        raise HTTPException(
            status_code=400,
            detail="phase must be one of: 'warm-up', 'main', 'cool-down'"
        )

    # Create request object
    try:
        request = RecommendationRequest(
            seed_artists=seed_artists_list,
            seed_tracks=seed_tracks_list,
            seed_genres=seed_genres_list,
            limit=limit,
            market=market,
            min_energy=min_energy,
            max_energy=max_energy,
            target_energy=target_energy,
            min_tempo=min_tempo,
            max_tempo=max_tempo,
            target_tempo=target_tempo,
            min_danceability=min_danceability,
            max_danceability=max_danceability,
            min_valence=min_valence,
            max_valence=max_valence,
            min_acousticness=min_acousticness,
            max_acousticness=max_acousticness,
            phase=phase,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        return await _get_recommendations_internal(
            request, spotify_service
        )
    except Exception as e:
        logger.error(f"Unexpected error in GET /recommendations: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

