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
            # Note: audio_features may return 403 if using client credentials
            # In that case, we'll skip BPM/energy and continue
            try:
                features = sp.audio_features([track_info["id"]])[0]
                if features and features.get("tempo"):
                    track_info["bpm"] = features.get("tempo", 0)
                    track_info["energy"] = features.get("energy", 0.5)
                else:
                    # Default values if features unavailable
                    track_info["bpm"] = 120  # Default BPM
                    track_info["energy"] = 0.5
            except Exception as e:
                # Log but don't fail - audio features are optional
                logger.debug(f"Could not get audio features for track {track_info['id']}: {e}")
                track_info["bpm"] = 120  # Default BPM
                track_info["energy"] = 0.5

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

        # Map genres to Spotify's valid seed genres
        # Spotify has a limited set of valid genres for recommendations
        valid_spotify_genres = {
            "acoustic", "afrobeat", "alt-rock", "alternative", "ambient", "anime",
            "black-metal", "bluegrass", "blues", "bossanova", "brazil", "breakbeat",
            "british", "cantopop", "chicago-house", "children", "chill", "classical",
            "club", "comedy", "country", "dance", "dancehall", "death-metal",
            "deep-house", "detroit-techno", "disco", "disney", "drum-and-bass",
            "dub", "dubstep", "edm", "electro", "electronic", "emo", "folk",
            "forro", "french", "funk", "garage", "german", "gospel", "goth",
            "grindcore", "groove", "grunge", "guitar", "happy", "hard-rock",
            "hardcore", "hardstyle", "heavy-metal", "hip-hop", "holidays",
            "honky-tonk", "house", "idm", "indian", "indie", "indie-pop",
            "industrial", "iranian", "j-dance", "j-idol", "j-pop", "j-rock",
            "jazz", "k-pop", "kids", "latin", "latino", "malay", "mandopop",
            "metal", "metal-misc", "metalcore", "minimal-techno", "movies",
            "mpb", "new-age", "new-release", "opera", "pagode", "party",
            "philippines-opm", "piano", "pop", "pop-film", "post-dubstep",
            "power-pop", "progressive-house", "psych-rock", "punk", "punk-rock",
            "r-n-b", "rainy-day", "reggae", "reggaeton", "road-trip", "rock",
            "rock-n-roll", "romance", "sad", "salsa", "samba", "sertanejo",
            "show-tunes", "singer-songwriter", "ska", "sleep", "songwriter",
            "soul", "soundtracks", "spanish", "study", "summer", "swedish",
            "synth-pop", "tango", "techno", "trance", "trip-hop", "turkish",
            "work-out", "world-music"
        }

        # Filter and map genres to valid Spotify genres
        valid_genres = []
        genre_mapping = {
            "chill": "chill",
            "ambient": "ambient",
            "classical": "classical",
            "jazz": "jazz",
            "folk": "folk",
            "electronic": "electronic",
            "edm": "edm",
            "house": "house",
            "techno": "techno",
            "trance": "trance",
            "rock": "rock",
            "pop": "pop",
            "hip-hop": "hip-hop",
            "r&b": "r-n-b",
            "rnb": "r-n-b",
            "country": "country",
            "reggae": "reggae",
            "metal": "metal",
            "punk": "punk",
            "indie": "indie",
            "acoustic": "acoustic",
            "dance": "dance",
            "disco": "disco",
            "funk": "funk",
            "soul": "soul",
            "blues": "blues",
            "latin": "latin",
            "world": "world-music",
        }

        for genre in genres[:5]:  # Max 5 genres
            genre_lower = genre.lower().strip()
            # Try direct match first
            if genre_lower in valid_spotify_genres:
                valid_genres.append(genre_lower)
            # Try mapping
            elif genre_lower in genre_mapping:
                mapped = genre_mapping[genre_lower]
                if mapped not in valid_genres:
                    valid_genres.append(mapped)
            # Try partial match
            else:
                for valid_genre in valid_spotify_genres:
                    if genre_lower in valid_genre or valid_genre in genre_lower:
                        if valid_genre not in valid_genres:
                            valid_genres.append(valid_genre)
                            break

        # If no valid genres found, use defaults
        if not valid_genres:
            logger.warning(f"No valid Spotify genres found from {genres}, using defaults")
            valid_genres = ["pop", "electronic"]  # Safe defaults

        # Get recommendations
        target_tempo = (bpm_min + bpm_max) / 2
        try:
            recommendations = sp.recommendations(
                seed_genres=valid_genres[:5],  # Max 5 genres
                target_tempo=target_tempo,
                min_tempo=bpm_min,
                max_tempo=bpm_max,
                target_energy=energy,
                limit=limit,
            )
        except Exception as e:
            logger.error(f"Spotify recommendations API error: {e}")
            # Return empty list instead of failing
            return json.dumps([], ensure_ascii=False)

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
            # Note: audio_features may return 403 if using client credentials
            try:
                features = sp.audio_features([track_info["id"]])[0]
                if features and features.get("tempo"):
                    track_info["bpm"] = features.get("tempo", 0)
                    track_info["energy"] = features.get("energy", 0.5)
                else:
                    track_info["bpm"] = 120  # Default BPM
                    track_info["energy"] = 0.5
            except Exception as e:
                logger.debug(f"Could not get audio features for track {track_info['id']}: {e}")
                track_info["bpm"] = 120  # Default BPM
                track_info["energy"] = 0.5

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

