"""
Spotify tools for LangChain agents.
"""
from typing import List, Dict, Optional, Tuple
from langchain.tools import tool
from loguru import logger

from app.services.spotify_service import SpotifyService
from app.core.config import settings

# Global Spotify service instance
_spotify_service = SpotifyService()


@tool
def search_spotify_tracks(
    query: str,
    genre: Optional[str] = None,
    bpm_min: Optional[int] = None,
    bpm_max: Optional[int] = None,
    limit: int = 20,
) -> str:
    """
    Search for tracks on Spotify.

    Args:
        query: Search query (track name, artist, or description)
        genre: Optional genre filter (e.g., "rock", "electronic")
        bpm_min: Optional minimum BPM
        bpm_max: Optional maximum BPM
        limit: Maximum number of tracks to return (default: 20)

    Returns:
        JSON string with list of tracks, each containing:
        - id: Spotify track ID
        - name: Track name
        - artist: Artist name
        - bpm: Track BPM (if available)
        - duration_ms: Duration in milliseconds
        - energy: Energy level (0-1)
        - genre: Primary genre
    """
    try:
        import json

        # Build search query
        search_query = query
        if genre:
            search_query = f"{query} genre:{genre}"

        # Use Spotify search
        sp = _spotify_service.get_user_client("")  # Will use client credentials
        # Actually, we need to use client credentials manager directly
        import spotipy
        from spotipy.oauth2 import SpotifyClientCredentials

        client_credentials = SpotifyClientCredentials(
            client_id=settings.SPOTIFY_CLIENT_ID,
            client_secret=settings.SPOTIFY_CLIENT_SECRET,
        )
        sp = spotipy.Spotify(client_credentials_manager=client_credentials)

        # Search for tracks
        results = sp.search(q=search_query, type="track", limit=limit)

        tracks = []
        for item in results.get("tracks", {}).get("items", []):
            track_info = {
                "id": item.get("id"),
                "name": item.get("name"),
                "artist": ", ".join([a["name"] for a in item.get("artists", [])]),
                "duration_ms": item.get("duration_ms", 0),
                "uri": item.get("uri"),
            }

            # Get audio features if available
            try:
                features = sp.audio_features([track_info["id"]])[0]
                if features:
                    track_info["bpm"] = features.get("tempo", 0)
                    track_info["energy"] = features.get("energy", 0.5)
            except Exception:
                pass

            # Filter by BPM if specified
            if bpm_min and track_info.get("bpm", 0) < bpm_min:
                continue
            if bpm_max and track_info.get("bpm", 0) > bpm_max:
                continue

            tracks.append(track_info)

        logger.info(f"Found {len(tracks)} tracks for query: {query}")
        return json.dumps(tracks, ensure_ascii=False)

    except Exception as e:
        logger.error(f"Error searching Spotify tracks: {e}")
        return json.dumps([])


@tool
def get_spotify_recommendations(
    genres: List[str],
    bpm_min: int,
    bpm_max: int,
    energy: float = 0.7,
    limit: int = 20,
) -> str:
    """
    Get track recommendations from Spotify based on genres and BPM.

    Args:
        genres: List of genres (e.g., ["rock", "electronic"])
        bpm_min: Minimum BPM
        bpm_max: Maximum BPM
        energy: Target energy level (0-1, default: 0.7)
        limit: Maximum number of tracks (default: 20)

    Returns:
        JSON string with list of recommended tracks
    """
    try:
        import json
        import spotipy
        from spotipy.oauth2 import SpotifyClientCredentials

        client_credentials = SpotifyClientCredentials(
            client_id=settings.SPOTIFY_CLIENT_ID,
            client_secret=settings.SPOTIFY_CLIENT_SECRET,
        )
        sp = spotipy.Spotify(client_credentials_manager=client_credentials)

        # Get recommendations
        target_tempo = (bpm_min + bpm_max) / 2
        recommendations = sp.recommendations(
            seed_genres=genres[:5],  # Max 5 genres
            target_tempo=target_tempo,
            min_tempo=bpm_min,
            max_tempo=bpm_max,
            target_energy=energy,
            limit=limit,
        )

        tracks = []
        for track in recommendations.get("tracks", []):
            track_info = {
                "id": track.get("id"),
                "name": track.get("name"),
                "artist": ", ".join([a["name"] for a in track.get("artists", [])]),
                "duration_ms": track.get("duration_ms", 0),
                "uri": track.get("uri"),
            }

            # Get audio features
            try:
                features = sp.audio_features([track_info["id"]])[0]
                if features:
                    track_info["bpm"] = features.get("tempo", 0)
                    track_info["energy"] = features.get("energy", 0.5)
            except Exception:
                pass

            tracks.append(track_info)

        logger.info(f"Got {len(tracks)} recommendations for genres: {genres}")
        return json.dumps(tracks, ensure_ascii=False)

    except Exception as e:
        logger.error(f"Error getting Spotify recommendations: {e}")
        return json.dumps([])


@tool
def calculate_bpm_progression(
    workout_type: str,
    duration_minutes: int,
    bpm_min: int,
    bpm_max: int,
) -> str:
    """
    Calculate BPM progression for workout phases.

    Args:
        workout_type: Type of workout (continuous/intervals/fartlek/recovery)
        duration_minutes: Total workout duration
        bpm_min: Minimum BPM
        bpm_max: Maximum BPM

    Returns:
        JSON string with BPM progression:
        - warmup: List of BPM values for warm-up
        - main: List of BPM values for main phase
        - cooldown: List of BPM values for cool-down
    """
    try:
        import json

        # Warm-up: gradually increase from bpm_min-20 to bpm_min
        warmup_duration = min(5, duration_minutes * 0.1)  # 10% or max 5 min
        warmup_steps = int(warmup_duration)
        warmup_bpm = [
            int(bpm_min - 20 + (20 * i / warmup_steps))
            for i in range(warmup_steps)
        ] if warmup_steps > 0 else [bpm_min]

        # Main phase: based on workout type
        main_duration = duration_minutes - warmup_duration - 5  # 5 min for cool-down
        main_steps = max(1, int(main_duration))

        if workout_type == "intervals":
            # Wave pattern for intervals
            main_bpm = []
            for i in range(main_steps):
                if i % 4 < 2:  # High intensity
                    main_bpm.append(bpm_max)
                else:  # Recovery
                    main_bpm.append(int((bpm_min + bpm_max) / 2))
        elif workout_type == "fartlek":
            # Variable pattern
            import random
            main_bpm = [
                random.randint(bpm_min, bpm_max)
                for _ in range(main_steps)
            ]
        else:
            # Steady or building
            if workout_type == "continuous":
                # Steady
                main_bpm = [int((bpm_min + bpm_max) / 2)] * main_steps
            else:
                # Building
                main_bpm = [
                    int(bpm_min + (bpm_max - bpm_min) * i / main_steps)
                    for i in range(main_steps)
                ]

        # Cool-down: gradually decrease from bpm_min to bpm_min-20
        cooldown_steps = 5
        cooldown_bpm = [
            int(bpm_min - (20 * i / cooldown_steps))
            for i in range(cooldown_steps)
        ]

        result = {
            "warmup": warmup_bpm,
            "main": main_bpm,
            "cooldown": cooldown_bpm,
        }

        return json.dumps(result)

    except Exception as e:
        logger.error(f"Error calculating BPM progression: {e}")
        return json.dumps({"warmup": [], "main": [], "cooldown": []})

