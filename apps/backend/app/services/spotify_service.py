"""
Spotify Service for API integration.
"""
from typing import Dict, List, Optional
import time
import hashlib
import json

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from app.core.config import settings
from loguru import logger


class SpotifyService:
    """Service for Spotify API operations."""

    def __init__(self):
        """Initialize Spotify client credentials."""
        # Validate credentials are set
        if (not settings.SPOTIFY_CLIENT_ID or
                not settings.SPOTIFY_CLIENT_SECRET):
            logger.error("Spotify credentials are missing!")
            raise ValueError(
                "SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET must be set"
            )

        # Log partial credentials for debugging (first 10 chars only)
        secret_display = (
            "*" * 10 if settings.SPOTIFY_CLIENT_SECRET else "MISSING"
        )
        logger.debug(
            f"Spotify Client ID: {settings.SPOTIFY_CLIENT_ID[:10]}... "
            f"Secret: {secret_display}"
        )
        self.client_credentials = SpotifyClientCredentials(
            client_id=settings.SPOTIFY_CLIENT_ID,
            client_secret=settings.SPOTIFY_CLIENT_SECRET,
        )

        # In-memory cache for optimized methods
        self._cache = {}
        self._cache_ttl = 3600  # 1 hour

        logger.info("SpotifyService initialized")

    def get_user_client(self, access_token: str) -> spotipy.Spotify:
        """
        Get Spotify client with user's access token.

        Args:
            access_token: User's Spotify access token

        Returns:
            Authenticated Spotify client
        """
        return spotipy.Spotify(auth=access_token)

    async def get_user_top_tracks(
        self,
        user_client: spotipy.Spotify,
        limit: int = 50,
    ) -> List[Dict]:
        """
        Get user's top tracks.

        Args:
            user_client: Authenticated Spotify client
            limit: Number of tracks to retrieve

        Returns:
            List of track dictionaries
        """
        try:
            results = user_client.current_user_top_tracks(
                limit=limit, time_range="medium_term"
            )
            return results.get("items", [])
        except Exception as e:
            logger.error(f"Failed to get user top tracks: {e}")
            raise

    async def get_user_top_artists(
        self,
        user_client: spotipy.Spotify,
        limit: int = 20,
    ) -> List[Dict]:
        """
        Get user's top artists.

        Args:
            user_client: Authenticated Spotify client
            limit: Number of artists to retrieve

        Returns:
            List of artist dictionaries
        """
        try:
            results = user_client.current_user_top_artists(
                limit=limit, time_range="medium_term"
            )
            return results.get("items", [])
        except Exception as e:
            logger.error(f"Failed to get user top artists: {e}")
            raise

    async def get_tracks_by_search(
        self,
        seed_genres: List[str],
        min_tempo: int,
        max_tempo: int,
        target_energy: float,
        limit: int = 20,
        search_query: Optional[str] = None,
    ) -> List[Dict]:
        """
        Get tracks using Search API as fallback when Recommendations fails.
        Searches for tracks and filters by audio features.

        Args:
            seed_genres: List of genre seeds
            min_tempo: Minimum BPM
            max_tempo: Maximum BPM
            target_energy: Target energy level (0-1)
            limit: Number of tracks to return

        Returns:
            List of track dictionaries with audio features
        """
        try:
            sp = spotipy.Spotify(
                client_credentials_manager=self.client_credentials
            )

            # Build search query - Spotify Search API doesn't support
            # genre: syntax well. Use more general search terms.
            # PRIORITY: Always prioritize dynamic workout music
            genres = seed_genres[:2] if seed_genres else ["pop", "rock"]

            # Try multiple search strategies (workout-focused)
            search_queries = []

            # Strategy 1: Genre + Workout keywords (HIGHEST PRIORITY)
            # Combine genres with dynamic workout keywords for best results
            for genre in genres:
                genre_map = {
                    "pop": "pop music",
                    "rock": "rock music",
                    "electronic": "electronic music",
                    "hip-hop": "hip hop",
                    "r&b": "r&b music",
                    "country": "country music",
                    "jazz": "jazz music",
                    "classical": "classical music",
                    "reggae": "reggae music",
                    "metal": "metal music",
                    "indie": "indie music",
                    "alternative": "alternative music",
                    "dance": "dance music",
                    "house": "house music",
                    "techno": "techno music",
                    "edm": "edm music",
                    "trance": "trance music",
                }
                genre_term = genre_map.get(genre.lower(), genre)

                # Add workout-focused queries with genre
                search_queries.append(f"{genre_term} workout")
                search_queries.append(f"{genre_term} fitness")
                search_queries.append(f"{genre_term} energetic")
                search_queries.append(f"{genre_term} upbeat")
                search_queries.append(f"{genre_term} running")

            # Strategy 2: If prompt provided, combine with workout keywords
            if search_query and search_query.strip():
                prompt_clean = search_query.strip()[:80]
                # Add workout context to user prompt
                search_queries.insert(0, f"{prompt_clean} workout")
                search_queries.insert(1, f"{prompt_clean} fitness")
                search_queries.insert(2, prompt_clean)

            # Strategy 3: General workout music queries (fallback)
            if not search_queries or len(search_queries) < 5:
                search_queries.extend([
                    "workout music",
                    "fitness music",
                    "gym music",
                    "running music",
                    "energetic music",
                    "upbeat workout",
                    "dynamic fitness",
                    "motivational workout"
                ])

            # Try each query until we get results
            tracks = []
            for query in search_queries:
                try:
                    logger.debug(f"Searching tracks with query: {query}")
                    search_results = sp.search(
                        q=query,
                        type="track",
                        limit=min(50, limit * 3),  # Get more to filter
                        market="US"
                    )

                    found_tracks = search_results.get(
                        "tracks", {}).get("items", [])
                    if found_tracks:
                        tracks.extend(found_tracks)
                        logger.debug(
                            f"Found {len(found_tracks)} tracks with query: {query}")
                        # If we have enough tracks, break
                        if len(tracks) >= limit:
                            break
                except Exception as search_error:
                    logger.warning(
                        f"Search query '{query}' failed: {search_error}")
                    continue

            if not tracks:
                logger.warning("No tracks found in any search query")
                # Final fallback: search for dynamic workout music
                try:
                    logger.debug(
                        "Trying final fallback: dynamic workout music")
                    fallback_queries = [
                        "workout music energetic",
                        "fitness music upbeat",
                        "gym music dynamic",
                        "running music motivational",
                        "cardio workout music",
                        "high energy workout"
                    ]
                    for fallback_query in fallback_queries:
                        try:
                            search_results = sp.search(
                                q=fallback_query,
                                type="track",
                                limit=limit,
                                market="US"
                            )
                            found_tracks = search_results.get(
                                "tracks", {}).get("items", [])
                            if found_tracks:
                                tracks.extend(found_tracks)
                                logger.debug(
                                    f"Found {len(found_tracks)} tracks "
                                    f"with fallback query: {fallback_query}"
                                )
                                if len(tracks) >= limit:
                                    break
                        except Exception:
                            continue
                except Exception as fallback_error:
                    logger.error(
                        f"Final fallback search also failed: {fallback_error}")
                    return []

            # Get track IDs
            track_ids = [t["id"] for t in tracks if t.get("id")]

            if not track_ids:
                logger.warning("No valid track IDs found")
                return []

            # Try to get audio features for filtering
            # If this fails (403), we'll return tracks without filtering
            features_list = []
            try:
                features_list = await self.get_audio_features_batch(track_ids)
                logger.debug(
                    f"Got audio features for {len(features_list)} tracks"
                )
            except Exception as features_error:
                error_str = str(features_error).lower()
                if "403" in error_str or "forbidden" in error_str:
                    logger.warning(
                        "Audio features API not available (403). "
                        "Returning tracks without tempo/energy filtering"
                    )
                else:
                    logger.warning(
                        f"Failed to get audio features: {features_error}. "
                        "Returning tracks without filtering"
                    )

            # If we have features, filter by tempo and energy
            if features_list:
                filtered_tracks = []
                for i, track in enumerate(tracks):
                    if i >= len(features_list) or not features_list[i]:
                        continue

                    features = features_list[i]
                    tempo = features.get("tempo", 0)
                    energy = features.get("energy", 0)

                    # Check if track matches criteria
                    # PRIORITY: Always prioritize dynamic, energetic tracks
                    # Minimum energy: 0.6 for workouts (80% of default 0.7)
                    min_energy = max(0.6, target_energy * 0.8)

                    if (min_tempo <= tempo <= max_tempo and
                            energy >= min_energy):
                        # Merge track info with features
                        track.update(features)
                        filtered_tracks.append(track)

                        if len(filtered_tracks) >= limit:
                            break

                # Sort by energy (descending) to prioritize dynamic tracks
                filtered_tracks.sort(
                    key=lambda x: x.get("energy", 0), reverse=True
                )

                logger.info(
                    f"Found {len(filtered_tracks)} tracks matching criteria "
                    f"from {len(tracks)} searched"
                )
                return filtered_tracks
            else:
                # No features available - return tracks as-is
                # Add default audio features values
                logger.info(
                    f"Returning {min(limit, len(tracks))} tracks "
                    "without audio features filtering"
                )
                result_tracks = []
                for track in tracks[:limit]:
                    # Add default audio features
                    track.update({
                        "tempo": (min_tempo + max_tempo) / 2,
                        "energy": target_energy,
                        "danceability": 0.7,
                        "valence": 0.7,
                    })
                    result_tracks.append(track)
                return result_tracks

        except Exception as e:
            logger.error(f"Failed to get tracks by search: {e}")
            raise

    async def get_recommendations(
        self,
        seed_genres: List[str],
        seed_artists: List[str],
        target_tempo: int,
        min_tempo: int,
        max_tempo: int,
        target_energy: float,
        limit: int = 20,
    ) -> List[Dict]:
        """
        Get track recommendations from Spotify.

        Args:
            seed_genres: List of genre seeds (max 2)
            seed_artists: List of artist IDs (max 2)
            target_tempo: Target BPM
            min_tempo: Minimum BPM
            max_tempo: Maximum BPM
            target_energy: Target energy level (0-1)
            limit: Number of recommendations

        Returns:
            List of track dictionaries with audio features
        """
        try:
            # Create Spotify client - ensure credentials are valid
            try:
                sp = spotipy.Spotify(
                    client_credentials_manager=self.client_credentials
                )

                # Test authentication by getting access token
                try:
                    token_info = self.client_credentials.get_access_token()
                    if not token_info:
                        logger.error(
                            "Failed to get Spotify access token - "
                            "credentials may be invalid"
                        )
                        raise Exception(
                            "Spotify authentication failed: "
                            "no access token received"
                        )
                    logger.debug("Spotify access token obtained successfully")
                except Exception as token_error:
                    logger.error(
                        f"Failed to get Spotify access token: {token_error}"
                    )
                    raise Exception(
                        f"Spotify authentication failed: {token_error}"
                    )
            except Exception as auth_error:
                logger.error(f"Failed to create Spotify client: {auth_error}")
                raise

            # Spotify API requires at least one seed (genre, artist, or track)
            # Must have at least 1 seed, max 5 total seeds
            seed_genres_list = list(seed_genres[:2]) if seed_genres else []
            seed_artists_list = list(seed_artists[:2]) if seed_artists else []
            seed_tracks_list = []

            # Always try to get seed_tracks first - they're more reliable
            # than seed_genres with Client Credentials
            # Even if genres are provided, try to get tracks for better results
            logger.debug(
                f"Attempting to get seed tracks (genres: {seed_genres_list}, artists: {seed_artists_list})"
            )
            try:
                # OPTIMIZATION: Method 1: Use optimized parallel method for seed tracks
                if seed_genres_list and len(seed_tracks_list) < 5:
                    try:
                        # Використовуємо оптимізований метод з паралельними запитами
                        seed_tracks_list = await self.get_seed_tracks_from_genres(
                            seed_genres_list,
                            limit_per_genre=3,
                            user_token=None  # Client Credentials для цього контексту
                        )
                        if seed_tracks_list:
                            logger.debug(
                                f"Got {len(seed_tracks_list)} seed tracks from optimized method")
                    except Exception as optimized_error:
                        logger.debug(
                            f"Optimized seed tracks method failed: {optimized_error}, using fallback")
                        # Fallback до послідовного пошуку
                        for genre in seed_genres_list[:2]:
                            try:
                                genre_map = {
                                    "pop": "pop music",
                                    "rock": "rock music",
                                    "electronic": "electronic music",
                                    "hip-hop": "hip hop",
                                    "country": "country music",
                                    "house": "house music",
                                    "techno": "techno music",
                                    "dance": "dance music",
                                }
                                search_term = genre_map.get(
                                    genre.lower(), genre)
                                search_results = sp.search(
                                    q=search_term,
                                    type="track",
                                    limit=5,
                                    market="US"
                                )
                                tracks = search_results.get(
                                    "tracks", {}).get("items", [])
                                for track in tracks:
                                    if track.get("id") and track["id"] not in seed_tracks_list:
                                        seed_tracks_list.append(track["id"])
                                        if len(seed_tracks_list) >= 5:
                                            break
                                if len(seed_tracks_list) >= 5:
                                    break
                            except Exception as genre_search_error:
                                logger.debug(
                                    f"Genre search for {genre} failed: {genre_search_error}")
                                continue

                # Method 2: If still no tracks, try featured playlists
                if len(seed_tracks_list) < 3:
                    try:
                        featured = sp.featured_playlists(limit=1)
                        playlists = featured.get(
                            "playlists", {}).get("items", [])
                        if playlists:
                            playlist_id = playlists[0]["id"]
                            playlist_tracks = sp.playlist_tracks(
                                playlist_id, limit=5)
                            for item in playlist_tracks.get("items", []):
                                if item.get("track") and item["track"].get("id"):
                                    track_id = item["track"]["id"]
                                    if track_id not in seed_tracks_list:
                                        seed_tracks_list.append(track_id)
                                        if len(seed_tracks_list) >= 5:
                                            break
                        if seed_tracks_list:
                            logger.debug(
                                f"Found {len(seed_tracks_list)} tracks from featured playlist"
                            )
                    except Exception as playlist_error:
                        logger.debug(
                            f"Featured playlists failed: {playlist_error}")

                # Method 3: Final fallback - search for popular tracks
                if len(seed_tracks_list) < 3:
                    try:
                        search_results = sp.search(
                            q="year:2023 OR year:2024",
                            type="track",
                            limit=5,
                            market="US"
                        )
                        tracks = search_results.get(
                            "tracks", {}).get("items", [])
                        for track in tracks:
                            if track.get("id") and track["id"] not in seed_tracks_list:
                                seed_tracks_list.append(track["id"])
                                if len(seed_tracks_list) >= 5:
                                    break
                        if seed_tracks_list:
                            logger.debug(
                                f"Found {len(seed_tracks_list)} tracks from popular search"
                            )
                    except Exception as search_error:
                        logger.warning(
                            f"Popular search failed: {search_error}")

                # If still no tracks, use default genres
                if not seed_tracks_list:
                    if not seed_genres_list:
                        seed_genres_list = ["pop", "rock"]
                    logger.debug("Using genres as seeds (no tracks found)")
            except Exception as general_error:
                logger.warning(
                    f"Failed to get seed tracks: {general_error}. "
                    "Using genres as fallback"
                )
                if not seed_genres_list:
                    seed_genres_list = ["pop", "rock"]

            # Build recommendations parameters
            # Start with minimal required parameters
            rec_params = {
                "limit": limit,
                "target_energy": target_energy,
            }

            # Add tempo parameters
            # NOTE: Spotify API may reject requests with target_tempo +
            # min/max_tempo together. Start with just min/max_tempo
            # to define the range
            rec_params["min_tempo"] = min_tempo
            rec_params["max_tempo"] = max_tempo
            # Don't add target_tempo initially - will retry with it if needed

            # Add seeds (at least one required)
            # spotipy expects lists, not strings
            # Prefer seed_tracks over seed_genres (more reliable)
            if seed_tracks_list:
                rec_params["seed_tracks"] = seed_tracks_list[:5]
                logger.debug(f"Using {len(seed_tracks_list)} track seeds")
            else:
                if seed_genres_list:
                    rec_params["seed_genres"] = seed_genres_list
                if seed_artists_list:
                    rec_params["seed_artists"] = seed_artists_list

            logger.debug(f"Spotify recommendations params: {rec_params}")

            # Try the request - start without target_tempo to avoid conflicts
            results = None
            last_error = None

            try:
                # First attempt: min/max_tempo only (no target_tempo)
                logger.debug(
                    f"Attempting recommendations with params: {rec_params}"
                )
                results = sp.recommendations(**rec_params)
                logger.debug("Recommendations request successful")
            except Exception as spotify_error:
                last_error = spotify_error
                error_str = str(spotify_error).lower()
                logger.warning(f"Recommendations failed: {spotify_error}")

                # Check if it's a 404 error (API not available or not accessible)
                is_404_error = (
                    "404" in error_str or
                    "not found" in error_str or
                    "http status: 404" in error_str
                )

                # Check if it's an HTTP error that might have status code
                status_code = None
                if hasattr(spotify_error, 'http_status'):
                    status_code = spotify_error.http_status
                elif hasattr(spotify_error, 'code'):
                    status_code = spotify_error.code

                if status_code == 404:
                    is_404_error = True

                # If 404, Recommendations API is not available
                # (likely no extended quota)
                # Immediately use Search API fallback without
                # trying other variations
                if is_404_error:
                    logger.error(
                        "404 error - Recommendations API not available. "
                        "This may indicate: "
                        "1) App doesn't have extended quota access, "
                        "2) Client Credentials don't have access, or "
                        "3) Spotify API endpoint issue. "
                        "Falling back to Search API immediately."
                    )

                    # Immediately use Search API fallback
                    # (no point trying other Recommendations variations)
                    logger.info(
                        "Recommendations API returned 404, "
                        "using Search API fallback immediately"
                    )
                    try:
                        return await self.get_tracks_by_search(
                            seed_genres=seed_genres_list,
                            min_tempo=min_tempo,
                            max_tempo=max_tempo,
                            target_energy=target_energy,
                            limit=limit,
                        )
                    except Exception as search_error:
                        logger.error(
                            f"Search API fallback failed: {search_error}"
                        )
                        raise Exception(
                            f"Spotify API request failed. "
                            f"Recommendations API returned 404 and "
                            f"Search API also failed. "
                            f"Search error: {search_error}"
                        )
                # For parameter errors, try without tempo parameters first
                elif "parameter" in error_str or "invalid" in error_str:
                    logger.warning(
                        "Parameter error detected, "
                        "trying without tempo constraints"
                    )
                    rec_params_no_tempo = {
                        "limit": limit,
                        "target_energy": target_energy,
                    }
                    # Try seed_tracks first (most reliable)
                    if seed_tracks_list:
                        rec_params_no_tempo["seed_tracks"] = (
                            seed_tracks_list[:5]
                        )  # noqa: E501
                    else:
                        if seed_genres_list:
                            rec_params_no_tempo["seed_genres"] = (
                                seed_genres_list
                            )
                        if seed_artists_list:
                            rec_params_no_tempo["seed_artists"] = (
                                seed_artists_list
                            )
                    logger.debug(
                        f"Retry params (no tempo): {rec_params_no_tempo}"
                    )
                    try:
                        results = sp.recommendations(**rec_params_no_tempo)
                        logger.info(
                            "Recommendations request successful without tempo"
                        )
                    except Exception as e2:
                        last_error = e2
                        error_str2 = str(e2).lower()
                        logger.warning(
                            f"Retry without tempo also failed: {e2}"
                        )

                        # If retry also fails, fallback to Search API
                        if ("404" in error_str2 or
                                "not found" in error_str2 or
                                "parameter" in error_str2):
                            logger.info(
                                "Retry without tempo failed, "
                                "falling back to Search API"
                            )
                            try:
                                return await self.get_tracks_by_search(
                                    seed_genres=seed_genres_list,
                                    min_tempo=min_tempo,
                                    max_tempo=max_tempo,
                                    target_energy=target_energy,
                                    limit=limit,
                                )
                            except Exception as search_error:
                                logger.error(
                                    f"Search API fallback failed: "
                                    f"{search_error}"
                                )
                                raise Exception(
                                    f"Spotify API request failed. "
                                    f"Recommendations API parameter errors "
                                    f"and Search API also failed. "
                                    f"Last error: {last_error}, "
                                    f"Search error: {search_error}"
                                )
                        else:
                            raise
                else:
                    # For other errors, try Search API as fallback
                    # before raising
                    logger.warning(
                        f"Unknown error type: {error_str[:100]}. "
                        "Trying Search API as fallback"
                    )
                    try:
                        return await self.get_tracks_by_search(
                            seed_genres=seed_genres_list,
                            min_tempo=min_tempo,
                            max_tempo=max_tempo,
                            target_energy=target_energy,
                            limit=limit,
                        )
                    except Exception as search_error:
                        logger.error(
                            f"Search API fallback failed: {search_error}"
                        )
                        # If Search API also fails, raise the original error
                        raise Exception(
                            f"Spotify API request failed. "
                            f"Recommendations API error: {last_error}. "
                            f"Search API fallback also failed: "
                            f"{search_error}"
                        )

            if results is None:
                logger.error("All recommendation attempts failed")
                if last_error:
                    raise last_error
                raise Exception("Failed to get recommendations from Spotify")

            tracks = results.get("tracks", [])

            if not tracks:
                logger.warning(
                    "No tracks returned from Spotify recommendations")
                return []

            # Get audio features for all tracks (using optimized method)
            track_ids = [track["id"] for track in tracks]
            features = await self.get_audio_features_batch_optimized(
                track_ids=track_ids,
                batch_size=100,
                user_token=None  # Client Credentials
            )

            # Merge track info with audio features
            for i, track in enumerate(tracks):
                if i < len(features) and features[i]:
                    track.update(features[i])

            return tracks

        except Exception as e:
            logger.error(f"Failed to get recommendations: {e}")
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")
            raise

    async def get_recommendations_advanced(
        self,
        seed_artists: Optional[List[str]] = None,
        seed_tracks: Optional[List[str]] = None,
        seed_genres: Optional[List[str]] = None,
        limit: int = 20,
        market: str = "US",
        min_energy: Optional[float] = None,
        max_energy: Optional[float] = None,
        target_energy: Optional[float] = None,
        min_tempo: Optional[float] = None,
        max_tempo: Optional[float] = None,
        target_tempo: Optional[float] = None,
        min_danceability: Optional[float] = None,
        max_danceability: Optional[float] = None,
        min_valence: Optional[float] = None,
        max_valence: Optional[float] = None,
        min_acousticness: Optional[float] = None,
        max_acousticness: Optional[float] = None,
    ) -> List[Dict]:
        """
        Get track recommendations from Spotify with advanced filters.

        Args:
            seed_artists: List of Spotify artist IDs (max 5)
            seed_tracks: List of Spotify track IDs (max 5)
            seed_genres: List of seed genres (max 5)
            limit: Number of recommendations (1-100)
            market: ISO country code
            min_energy: Minimum energy (0-1)
            max_energy: Maximum energy (0-1)
            target_energy: Target energy (0-1)
            min_tempo: Minimum tempo/BPM (0-250)
            max_tempo: Maximum tempo/BPM (0-250)
            target_tempo: Target tempo/BPM (0-250)
            min_danceability: Minimum danceability (0-1)
            max_danceability: Maximum danceability (0-1)
            min_valence: Minimum valence (0-1)
            max_valence: Maximum valence (0-1)
            min_acousticness: Minimum acousticness (0-1)
            max_acousticness: Maximum acousticness (0-1)

        Returns:
            List of track dictionaries with audio features

        Raises:
            ValueError: If no seeds provided or invalid parameters
            Exception: If Spotify API call fails
        """
        try:
            import spotipy

            # Validate seeds
            seed_artists_list = list(seed_artists) if seed_artists else []
            seed_tracks_list = list(seed_tracks) if seed_tracks else []
            seed_genres_list = list(seed_genres) if seed_genres else []

            # Trim seeds to max 5 total
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

            # Ensure at least one seed
            if (
                not seed_artists_list and
                not seed_tracks_list and
                not seed_genres_list
            ):
                raise ValueError(
                    "At least one of seed_artists, seed_tracks, "
                    "or seed_genres must be provided"
                )

            # Create Spotify client
            sp = spotipy.Spotify(
                client_credentials_manager=self.client_credentials
            )

            # Build recommendations parameters
            rec_params = {
                "limit": min(limit, 100),  # Spotify max is 100
                "market": market,
            }

            # Add seeds
            if seed_tracks_list:
                rec_params["seed_tracks"] = seed_tracks_list[:5]
            if seed_artists_list:
                rec_params["seed_artists"] = seed_artists_list[:5]
            if seed_genres_list:
                rec_params["seed_genres"] = seed_genres_list[:5]

            # Add energy filters
            if min_energy is not None:
                rec_params["min_energy"] = min_energy
            if max_energy is not None:
                rec_params["max_energy"] = max_energy
            if target_energy is not None:
                rec_params["target_energy"] = target_energy

            # Add tempo filters
            # Note: Spotify may reject target_tempo with min/max_tempo
            # Try min/max first, then target_tempo if needed
            if min_tempo is not None:
                rec_params["min_tempo"] = min_tempo
            if max_tempo is not None:
                rec_params["max_tempo"] = max_tempo
            if target_tempo is not None and "min_tempo" not in rec_params:
                # Only add target_tempo if min_tempo not set
                rec_params["target_tempo"] = target_tempo

            # Add danceability filters
            if min_danceability is not None:
                rec_params["min_danceability"] = min_danceability
            if max_danceability is not None:
                rec_params["max_danceability"] = max_danceability

            # Add valence filters
            if min_valence is not None:
                rec_params["min_valence"] = min_valence
            if max_valence is not None:
                rec_params["max_valence"] = max_valence

            # Add acousticness filters
            if min_acousticness is not None:
                rec_params["min_acousticness"] = min_acousticness
            if max_acousticness is not None:
                rec_params["max_acousticness"] = max_acousticness

            logger.debug(f"Spotify recommendations params: {rec_params}")

            # Try the request
            try:
                results = sp.recommendations(**rec_params)
                logger.debug("Recommendations request successful")
            except Exception as spotify_error:
                error_str = str(spotify_error).lower()
                logger.warning(f"Recommendations failed: {spotify_error}")

                # If error with tempo parameters, try without target_tempo
                if (
                    "404" in error_str or
                    "parameter" in error_str or
                    "invalid" in error_str
                ) and target_tempo is not None:
                    logger.info("Retrying without target_tempo")
                    rec_params_no_target = rec_params.copy()
                    rec_params_no_target.pop("target_tempo", None)
                    try:
                        results = sp.recommendations(**rec_params_no_target)
                        logger.debug(
                            "Recommendations successful without target_tempo"
                        )
                    except Exception as e2:
                        logger.error(f"Retry also failed: {e2}")
                        raise
                else:
                    raise

            tracks = results.get("tracks", [])

            if not tracks:
                logger.warning(
                    "No tracks returned from Spotify recommendations")
                return []

            # Get audio features for all tracks
            track_ids = [track["id"] for track in tracks if track.get("id")]
            features = await self.get_audio_features_batch_optimized(
                track_ids=track_ids,
                batch_size=100,
                user_token=None  # Client Credentials
            )

            # Merge track info with audio features
            for i, track in enumerate(tracks):
                if i < len(features) and features[i]:
                    track.update(features[i])

            return tracks

        except Exception as e:
            logger.error(f"Failed to get recommendations: {e}")
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")
            raise

    async def get_audio_features_batch(
        self,
        track_ids: List[str],
    ) -> List[Optional[Dict]]:
        """
        Get audio features for multiple tracks (batch).

        OPTIMIZATION: Використовує оптимізований метод з паралельними запитами.

        Args:
            track_ids: List of Spotify track IDs

        Returns:
            List of audio features dictionaries

        Raises:
            Exception: If API call fails (403, 404, etc.)
        """
        # Використовуємо оптимізований метод
        return await self.get_audio_features_batch_optimized(
            track_ids=track_ids,
            batch_size=100,
            user_token=None  # Client Credentials
        )

    async def search_track_by_name(
        self,
        track_name: str,
        artist_name: Optional[str] = None,
        limit: int = 1,
    ) -> Optional[Dict]:
        """
        Search for a specific track by name and optionally artist.

        Args:
            track_name: Track name
            artist_name: Optional artist name for better matching
            limit: Number of results to return (default 1 for best match)

        Returns:
            Track dictionary if found, None otherwise
        """
        try:
            sp = spotipy.Spotify(
                client_credentials_manager=self.client_credentials
            )

            # Build search query
            if artist_name:
                query = f"track:{track_name} artist:{artist_name}"
            else:
                query = f"track:{track_name}"

            search_results = sp.search(
                q=query,
                type="track",
                limit=limit,
                market="US"
            )

            tracks = search_results.get("tracks", {}).get("items", [])
            if tracks:
                return tracks[0]
            return None

        except Exception as e:
            logger.warning(
                f"Failed to search track '{track_name}' by '{artist_name}': {e}")
            return None

    async def create_playlist(
        self,
        user_client: spotipy.Spotify,
        user_id: str,
        name: str,
        tracks: List[str],  # Spotify URIs
        description: str = "Generated by RunBeat AI",
    ) -> Dict:
        """
        Create playlist in user's Spotify account.

        Args:
            user_client: Authenticated Spotify client
            user_id: Spotify user ID
            name: Playlist name
            tracks: List of Spotify track URIs
            description: Playlist description

        Returns:
            Dictionary with playlist ID, URL, and URI
        """
        try:
            # Create playlist
            playlist = user_client.user_playlist_create(
                user=user_id,
                name=name,
                public=False,
                description=description,
            )

            # Add tracks in batches (max 100 per request)
            if tracks:
                for i in range(0, len(tracks), 100):
                    batch = tracks[i: i + 100]
                    user_client.playlist_add_items(
                        playlist_id=playlist["id"],
                        items=batch,
                    )

            return {
                "id": playlist["id"],
                "url": playlist["external_urls"]["spotify"],
                "uri": playlist["uri"],
            }

        except Exception as e:
            logger.error(f"Failed to create playlist: {e}")
            raise

    # ========== OPTIMIZED METHODS ==========
    # These methods provide better performance with User Authorization
    # and caching support

    def _get_cache_key(
        self,
        seed_genres: List[str],
        min_tempo: int,
        max_tempo: int,
        target_energy: float,
        user_token: Optional[str] = None
    ) -> str:
        """Generate cache key from parameters."""
        key_data = {
            "genres": sorted(seed_genres) if seed_genres else [],
            "min_tempo": min_tempo,
            "max_tempo": max_tempo,
            "target_energy": target_energy,
            "user_token": bool(user_token)  # Don't cache token itself
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()

    async def get_seed_tracks_from_genres(
        self,
        genres: List[str],
        limit_per_genre: int = 5,
        user_token: Optional[str] = None
    ) -> List[str]:
        """
        Отримати seed tracks з жанрів (оптимізовано з паралельними запитами).

        Args:
            genres: Список жанрів
            limit_per_genre: Кількість треків на жанр
            user_token: User access token (опціонально)

        Returns:
            Список track IDs для використання як seeds
        """
        import asyncio

        genres = genres[:2] if genres else []
        if not genres:
            return []

        # Перевірка кешу
        cache_key = f"seed_tracks_{hash(tuple(sorted(genres)))}_{limit_per_genre}"
        if cache_key in self._cache:
            cached_data, timestamp = self._cache[cache_key]
            if time.time() - timestamp < 1800:  # 30 хвилин для seed tracks
                logger.debug(f"Cache hit for seed tracks: {genres}")
                return cached_data

        # Використовуємо User Auth якщо доступний, інакше Client Credentials
        if user_token:
            sp = spotipy.Spotify(auth=user_token)
        else:
            sp = spotipy.Spotify(
                client_credentials_manager=self.client_credentials
            )

        genre_map = {
            "pop": "pop music",
            "rock": "rock music",
            "electronic": "electronic music",
            "hip-hop": "hip hop",
            "country": "country music",
            "house": "house music",
            "techno": "techno music",
            "dance": "dance music",
            "r&b": "r&b music",
            "jazz": "jazz music",
            "edm": "edm music",
            "trance": "trance music",
        }

        # OPTIMIZATION: Паралельні запити для всіх жанрів одночасно
        async def search_genre(genre: str) -> List[str]:
            """Пошук треків для одного жанру."""
            try:
                search_term = genre_map.get(genre.lower(), genre)
                # Використовуємо run_in_executor для неблокуючих запитів
                loop = asyncio.get_event_loop()
                search_results = await loop.run_in_executor(
                    None,
                    lambda: sp.search(
                        q=search_term,
                        type="track",
                        limit=limit_per_genre,
                        market="US"
                    )
                )
                tracks = search_results.get("tracks", {}).get("items", [])
                return [track["id"] for track in tracks if track.get("id")]
            except Exception as e:
                logger.debug(f"Failed to get seed tracks for {genre}: {e}")
                return []

        # Виконуємо всі запити паралельно
        try:
            results = await asyncio.gather(*[search_genre(g) for g in genres])
            seed_tracks = []
            seen_ids = set()

            # Об'єднуємо результати, уникаючи дублікатів
            for track_ids in results:
                for track_id in track_ids:
                    if track_id not in seen_ids:
                        seed_tracks.append(track_id)
                        seen_ids.add(track_id)
                        if len(seed_tracks) >= 5:
                            break
                if len(seed_tracks) >= 5:
                    break
        except Exception as e:
            logger.warning(
                f"Parallel seed tracks search failed: {e}, falling back to sequential")
            # Fallback до послідовного пошуку
            seed_tracks = []
            for genre in genres:
                try:
                    search_term = genre_map.get(genre.lower(), genre)
                    search_results = sp.search(
                        q=search_term,
                        type="track",
                        limit=limit_per_genre,
                        market="US"
                    )
                    tracks = search_results.get("tracks", {}).get("items", [])
                    for track in tracks:
                        if track.get("id") and track["id"] not in seed_tracks:
                            seed_tracks.append(track["id"])
                            if len(seed_tracks) >= 5:
                                break
                    if len(seed_tracks) >= 5:
                        break
                except Exception as e:
                    logger.warning(
                        f"Failed to get seed tracks for {genre}: {e}")
                    continue

        result = seed_tracks[:5]  # Max 5 seeds

        # Зберегти в кеш
        self._cache[cache_key] = (result, time.time())

        return result

    async def get_recommendations_optimized(
        self,
        seed_genres: List[str],
        seed_artists: List[str],
        target_tempo: int,
        min_tempo: int,
        max_tempo: int,
        target_energy: float,
        limit: int = 20,
        user_token: Optional[str] = None,
        use_cache: bool = True
    ) -> List[Dict]:
        """
        Оптимізований метод отримання рекомендацій.

        Strategy:
        1. Перевірка кешу
        2. Використання User Auth для Recommendations API
        3. Fallback до Search API з Client Credentials
        4. Batch запити для audio features
        """
        # Перевірка кешу
        if use_cache:
            cache_key = self._get_cache_key(
                seed_genres, min_tempo, max_tempo, target_energy, user_token
            )
            if cache_key in self._cache:
                cached_data, timestamp = self._cache[cache_key]
                if time.time() - timestamp < self._cache_ttl:
                    logger.debug(f"Cache hit for key: {cache_key}")
                    return cached_data[:limit]

        # Strategy 1: Recommendations API з User Auth
        if user_token:
            try:
                sp = spotipy.Spotify(auth=user_token)

                # Отримати seed tracks
                seed_tracks = await self.get_seed_tracks_from_genres(
                    seed_genres, user_token=user_token
                )

                if seed_tracks:
                    rec_params = {
                        "seed_tracks": seed_tracks[:5],
                        "min_tempo": min_tempo,
                        "max_tempo": max_tempo,
                        "target_energy": target_energy,
                        "limit": limit
                    }
                else:
                    rec_params = {
                        "seed_genres": seed_genres[:2] if seed_genres else ["pop"],
                        "min_tempo": min_tempo,
                        "max_tempo": max_tempo,
                        "target_energy": target_energy,
                        "limit": limit
                    }

                logger.debug(f"Using Recommendations API with User Auth")
                results = sp.recommendations(**rec_params)
                tracks = results.get("tracks", [])

                if tracks:
                    # Отримати audio features batch
                    track_ids = [t["id"] for t in tracks if t.get("id")]
                    features = await self.get_audio_features_batch_optimized(
                        track_ids, user_token=user_token
                    )

                    # Merge features with tracks
                    for i, track in enumerate(tracks):
                        if i < len(features) and features[i]:
                            track.update(features[i])

                    # Зберегти в кеш
                    if use_cache:
                        self._cache[cache_key] = (tracks, time.time())

                    return tracks

            except Exception as e:
                logger.warning(
                    f"Recommendations API with User Auth failed: {e}, "
                    "falling back to Search API"
                )

        # Strategy 2: Search API з Client Credentials (fallback)
        logger.debug("Using Search API with Client Credentials")
        tracks = await self.get_tracks_by_search_optimized(
            seed_genres=seed_genres,
            min_tempo=min_tempo,
            max_tempo=max_tempo,
            target_energy=target_energy,
            limit=limit
        )

        # Зберегти в кеш
        if use_cache and tracks:
            cache_key = self._get_cache_key(
                seed_genres, min_tempo, max_tempo, target_energy, user_token
            )
            self._cache[cache_key] = (tracks, time.time())

        return tracks

    async def get_tracks_by_search_optimized(
        self,
        seed_genres: List[str],
        min_tempo: int,
        max_tempo: int,
        target_energy: float,
        limit: int = 20,
        search_query: Optional[str] = None
    ) -> List[Dict]:
        """
        Оптимізований пошук треків через Search API.

        Покращення:
        - Кращий формат пошукових запитів
        - Batch запити для audio features
        - Кілька стратегій пошуку
        """
        try:
            sp = spotipy.Spotify(
                client_credentials_manager=self.client_credentials
            )

            genres = seed_genres[:2] if seed_genres else ["pop", "rock"]
            search_queries = []

            # PRIORITY: Always prioritize dynamic workout music
            # Strategy 1: Genre + Workout keywords (HIGHEST PRIORITY)
            genre_map = {
                "pop": "pop music",
                "rock": "rock music",
                "electronic": "electronic music",
                "hip-hop": "hip hop",
                "r&b": "r&b music",
                "country": "country music",
                "house": "house music",
                "techno": "techno music",
                "dance": "dance music",
                "edm": "edm music",
                "trance": "trance music",
                "metal": "metal music",
                "indie": "indie music",
            }

            for genre in genres:
                genre_term = genre_map.get(genre.lower(), genre)
                # Add workout-focused queries with genre
                search_queries.append(f"{genre_term} workout")
                search_queries.append(f"{genre_term} fitness")
                search_queries.append(f"{genre_term} energetic")
                search_queries.append(f"{genre_term} upbeat")
                search_queries.append(f"{genre_term} running")

            # Strategy 2: Prompt-based search with workout keywords
            if search_query and search_query.strip():
                prompt_clean = search_query.strip()[:80]
                # Add workout context to user prompt
                search_queries.insert(0, f"{prompt_clean} workout")
                search_queries.insert(1, f"{prompt_clean} fitness")
                search_queries.insert(2, prompt_clean)

            # Strategy 3: General workout music queries (fallback)
            if not search_queries or len(search_queries) < 5:
                search_queries.extend([
                    "workout music",
                    "fitness music",
                    "gym music",
                    "running music",
                    "energetic music",
                    "upbeat workout",
                    "dynamic fitness",
                    "motivational workout"
                ])

            # Try each query
            all_tracks = []
            all_track_ids = set()

            for query in search_queries:
                try:
                    search_results = sp.search(
                        q=query,
                        type="track",
                        limit=min(50, limit * 3),
                        market="US"
                    )
                    found_tracks = search_results.get(
                        "tracks", {}).get("items", [])

                    for track in found_tracks:
                        track_id = track.get("id")
                        if track_id and track_id not in all_track_ids:
                            all_tracks.append(track)
                            all_track_ids.add(track_id)
                            if len(all_tracks) >= limit * 2:
                                break

                    if len(all_tracks) >= limit * 2:
                        break
                except Exception as e:
                    logger.warning(f"Search query '{query}' failed: {e}")
                    continue

            # Final fallback: dynamic workout music
            if not all_tracks:
                fallback_queries = [
                    "workout music energetic",
                    "fitness music upbeat",
                    "gym music dynamic",
                    "running music motivational",
                    "cardio workout music",
                    "high energy workout"
                ]
                for fallback_query in fallback_queries:
                    try:
                        search_results = sp.search(
                            q=fallback_query,
                            type="track",
                            limit=limit,
                            market="US"
                        )
                        found_tracks = search_results.get(
                            "tracks", {}).get("items", [])
                        if found_tracks:
                            all_tracks.extend(found_tracks)
                            logger.debug(
                                f"Found {len(found_tracks)} tracks "
                                f"with fallback query: {fallback_query}"
                            )
                            if len(all_tracks) >= limit:
                                break
                    except Exception as e:
                        logger.warning(
                            f"Fallback query '{fallback_query}' failed: {e}"
                        )
                        continue

                if not all_tracks:
                    logger.error("Final fallback search failed")
                    return []

            # Batch запит для audio features
            track_ids = [t["id"] for t in all_tracks if t.get("id")]
            features = await self.get_audio_features_batch_optimized(track_ids)

            # Filter by tempo and energy
            filtered_tracks = []
            for i, track in enumerate(all_tracks):
                if i >= len(features) or not features[i]:
                    continue

                tempo = features[i].get("tempo", 0)
                energy = features[i].get("energy", 0)

                # PRIORITY: Always prioritize dynamic, energetic tracks
                # Minimum energy: 0.6 for workouts (80% of default 0.7)
                min_energy = max(0.6, target_energy * 0.8)

                if (min_tempo <= tempo <= max_tempo and
                        energy >= min_energy):
                    track.update(features[i])
                    filtered_tracks.append(track)
                    if len(filtered_tracks) >= limit * 2:
                        break

            # Sort by energy (descending) to prioritize dynamic tracks
            filtered_tracks.sort(
                key=lambda x: x.get("energy", 0), reverse=True
            )
            # Limit to requested number
            filtered_tracks = filtered_tracks[:limit]

            # Якщо не знайдено відповідних треків, повертаємо без фільтрації
            if not filtered_tracks:
                logger.warning(
                    "No tracks match tempo/energy criteria, "
                    "returning top results"
                )
                for i, track in enumerate(all_tracks[:limit]):
                    if i < len(features) and features[i]:
                        track.update(features[i])
                    else:
                        track.update({
                            "tempo": (min_tempo + max_tempo) / 2,
                            "energy": target_energy,
                            "danceability": 0.7,
                        })
                    filtered_tracks.append(track)

            return filtered_tracks[:limit]

        except Exception as e:
            logger.error(f"Failed to get tracks by search: {e}")
            raise

    async def get_audio_features_batch_optimized(
        self,
        track_ids: List[str],
        batch_size: int = 100,
        user_token: Optional[str] = None
    ) -> List[Optional[Dict]]:
        """
        Оптимізований batch запит для audio features з паралельними запитами.

        Spotify API дозволяє до 100 треків в одному запиті.
        OPTIMIZATION: Паралельна обробка батчів для швидшої роботи.
        """
        import asyncio

        if not track_ids:
            return []

        batch_size = min(batch_size, 100)  # Spotify limit

        # Перевірка кешу
        # Перші 50 для ключа
        cache_key = f"audio_features_{hash(tuple(track_ids[:50]))}"
        if cache_key in self._cache:
            cached_data, timestamp = self._cache[cache_key]
            if time.time() - timestamp < 3600:  # 1 година для audio features
                logger.debug(
                    f"Cache hit for audio features: {len(track_ids)} tracks")
                return cached_data

        # Використовуємо User Auth якщо доступний
        if user_token:
            sp = spotipy.Spotify(auth=user_token)
        else:
            sp = spotipy.Spotify(
                client_credentials_manager=self.client_credentials
            )

        # OPTIMIZATION: Паралельна обробка батчів
        async def fetch_batch(batch: List[str], batch_num: int) -> List[Optional[Dict]]:
            """Отримати audio features для одного батчу."""
            try:
                loop = asyncio.get_event_loop()
                batch_features = await loop.run_in_executor(
                    None,
                    lambda: sp.audio_features(batch)
                )
                if batch_features:
                    return batch_features
                else:
                    return [None] * len(batch)
            except Exception as e:
                error_str = str(e).lower()
                if "403" in error_str or "forbidden" in error_str:
                    logger.warning(
                        f"Audio features API returned 403 for batch {batch_num}. "
                        "This may indicate insufficient permissions."
                    )
                elif "429" in error_str or "rate limit" in error_str:
                    logger.warning(
                        f"Rate limit hit for batch {batch_num}, waiting 1s...")
                    await asyncio.sleep(1)
                    # Retry once
                    try:
                        loop = asyncio.get_event_loop()
                        batch_features = await loop.run_in_executor(
                            None,
                            lambda: sp.audio_features(batch)
                        )
                        return batch_features if batch_features else [None] * len(batch)
                    except Exception as retry_error:
                        logger.warning(
                            f"Retry failed for batch {batch_num}: {retry_error}")
                else:
                    logger.warning(f"Batch {batch_num} failed: {e}")
                return [None] * len(batch)

        # Розбиваємо на батчі та виконуємо паралельно
        batches = [track_ids[i:i + batch_size]
                   for i in range(0, len(track_ids), batch_size)]

        try:
            # Виконуємо всі батчі паралельно (але обмежуємо до 3 одночасно для rate limits)
            features = []
            semaphore = asyncio.Semaphore(3)  # Максимум 3 паралельні запити

            async def fetch_with_semaphore(batch: List[str], batch_num: int):
                async with semaphore:
                    return await fetch_batch(batch, batch_num)

            results = await asyncio.gather(*[
                fetch_with_semaphore(batch, i)
                for i, batch in enumerate(batches)
            ])

            # Об'єднуємо результати
            for result in results:
                features.extend(result)
        except Exception as e:
            logger.warning(
                f"Parallel batch fetch failed: {e}, falling back to sequential")
            # Fallback до послідовної обробки
            features = []
            for i, batch in enumerate(batches):
                try:
                    batch_features = sp.audio_features(batch)
                    if batch_features:
                        features.extend(batch_features)
                    else:
                        features.extend([None] * len(batch))
                except Exception as batch_error:
                    logger.warning(f"Batch {i} failed: {batch_error}")
                    features.extend([None] * len(batch))

        # Зберегти в кеш (тільки якщо успішно отримано більшість)
        if features and sum(1 for f in features if f is not None) > len(features) * 0.5:
            self._cache[cache_key] = (features, time.time())

        return features

    def clear_cache(self):
        """Очистити кеш."""
        self._cache.clear()
        logger.info("Cache cleared")

    def get_cache_stats(self) -> Dict:
        """Отримати статистику кешу."""
        return {
            "cache_size": len(self._cache),
            "cache_ttl": self._cache_ttl,
            "cached_keys": list(self._cache.keys())[:10]
        }
