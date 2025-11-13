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

            # Build search query - Spotify Search API doesn't support genre: syntax well
            # Use more general search terms
            genres = seed_genres[:2] if seed_genres else ["pop", "rock"]

            # Try multiple search strategies
            search_queries = []

            # Strategy 1: If prompt provided, use it as primary search
            if search_query and search_query.strip():
                prompt_clean = search_query.strip()[:100]
                search_queries.append(prompt_clean)

            # Strategy 2: Search for genre names as regular terms (not genre:)
            for genre in genres:
                # Map common genre names to searchable terms
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
                }
                search_term = genre_map.get(genre.lower(), genre)
                search_queries.append(search_term)

            # Strategy 3: Fallback to popular music if no results
            if not search_queries:
                search_queries = ["popular music", "top hits"]

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

                    found_tracks = search_results.get("tracks", {}).get("items", [])
                    if found_tracks:
                        tracks.extend(found_tracks)
                        logger.debug(f"Found {len(found_tracks)} tracks with query: {query}")
                        # If we have enough tracks, break
                        if len(tracks) >= limit:
                            break
                except Exception as search_error:
                    logger.warning(f"Search query '{query}' failed: {search_error}")
                    continue

            if not tracks:
                logger.warning("No tracks found in any search query")
                # Final fallback: search for "workout music" or "running music"
                try:
                    logger.debug("Trying final fallback: 'workout music'")
                    search_results = sp.search(
                        q="workout music OR running music",
                        type="track",
                        limit=limit,
                        market="US"
                    )
                    tracks = search_results.get("tracks", {}).get("items", [])
                    if tracks:
                        logger.debug(f"Found {len(tracks)} tracks with fallback query")
                except Exception as fallback_error:
                    logger.error(f"Final fallback search also failed: {fallback_error}")
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
                    if (min_tempo <= tempo <= max_tempo and
                            energy >= target_energy * 0.8):  # 80% of target
                        # Merge track info with features
                        track.update(features)
                        filtered_tracks.append(track)

                        if len(filtered_tracks) >= limit:
                            break

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
                # Method 1: Search for tracks by genre if genres provided
                if seed_genres_list and len(seed_tracks_list) < 5:
                    for genre in seed_genres_list[:2]:
                        try:
                            # Map genre names to searchable terms
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
                            search_term = genre_map.get(genre.lower(), genre)
                            search_results = sp.search(
                                q=search_term,
                                type="track",
                                limit=5,
                                market="US"
                            )
                            tracks = search_results.get("tracks", {}).get("items", [])
                            for track in tracks:
                                if track.get("id") and track["id"] not in seed_tracks_list:
                                    seed_tracks_list.append(track["id"])
                                    if len(seed_tracks_list) >= 5:
                                        break
                            if len(seed_tracks_list) >= 5:
                                break
                        except Exception as genre_search_error:
                            logger.debug(f"Genre search for {genre} failed: {genre_search_error}")
                            continue

                # Method 2: If still no tracks, try featured playlists
                if len(seed_tracks_list) < 3:
                    try:
                        featured = sp.featured_playlists(limit=1)
                        playlists = featured.get("playlists", {}).get("items", [])
                        if playlists:
                            playlist_id = playlists[0]["id"]
                            playlist_tracks = sp.playlist_tracks(playlist_id, limit=5)
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
                        logger.debug(f"Featured playlists failed: {playlist_error}")

                # Method 3: Final fallback - search for popular tracks
                if len(seed_tracks_list) < 3:
                    try:
                        search_results = sp.search(
                            q="year:2023 OR year:2024",
                            type="track",
                            limit=5,
                            market="US"
                        )
                        tracks = search_results.get("tracks", {}).get("items", [])
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
                        logger.warning(f"Popular search failed: {search_error}")

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

                # If 404, it might be authentication or endpoint issue
                # Recommendations API may not work with Client Credentials
                if "404" in error_str or "not found" in error_str:
                    logger.error(
                        "404 error - Recommendations API not available. "
                        "This may indicate: "
                        "1) Client Credentials don't have access, "
                        "2) Spotify API endpoint issue, or "
                        "3) Parameter format problem"
                    )

                    # If 404 on first try, immediately use Search API fallback
                    # Recommendations API likely doesn't work
                    # with Client Credentials
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
                        # Still try minimal request as last resort
                        logger.info(
                            "Retrying with minimal parameters "
                            "(no tempo constraints)"
                        )
                    rec_params_minimal = {
                        "limit": limit,
                        "target_energy": target_energy,
                    }
                    # Try seed_tracks first (most reliable)
                    if seed_tracks_list:
                        rec_params_minimal["seed_tracks"] = (
                            seed_tracks_list[:5]
                        )
                    else:
                        if seed_genres_list:
                            rec_params_minimal["seed_genres"] = (
                                seed_genres_list
                            )
                        if seed_artists_list:
                            rec_params_minimal["seed_artists"] = (
                                seed_artists_list
                            )
                    logger.debug(
                        f"Retry params (minimal): {rec_params_minimal}")
                    try:
                        results = sp.recommendations(**rec_params_minimal)
                        logger.info(
                            "Minimal request succeeded - "
                            "tempo parameters may be causing issues"
                        )
                    except Exception as e2:
                        last_error = e2
                        logger.error(f"Even minimal request failed: {e2}")
                        # Final fallback: use Search API instead
                        logger.info(
                            "Recommendations API failed, "
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
                        except Exception as search_fallback_error:
                            logger.error(
                                f"Search API fallback also failed: "
                                f"{search_fallback_error}"
                            )
                            raise Exception(
                                f"Spotify API request failed. "
                                f"Recommendations and Search both failed. "
                                f"Last error: {last_error}"
                            )
                # For other errors, try without tempo parameters
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
                    except Exception as e2:
                        last_error = e2
                        raise
                else:
                    # For other errors, raise immediately
                    raise

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

            # Get audio features for all tracks
            track_ids = [track["id"] for track in tracks]
            features = await self.get_audio_features_batch(track_ids)

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

        Args:
            track_ids: List of Spotify track IDs

        Returns:
            List of audio features dictionaries

        Raises:
            Exception: If API call fails (403, 404, etc.)
        """
        try:
            sp = spotipy.Spotify(
                client_credentials_manager=self.client_credentials
            )

            # Spotify API allows max 100 tracks per request
            # Try smaller batches if we get errors
            features = []
            batch_size = 100

            for i in range(0, len(track_ids), batch_size):
                batch = track_ids[i: i + batch_size]
                try:
                    batch_features = sp.audio_features(batch)
                    if batch_features:
                        features.extend(batch_features)
                    else:
                        # If no features returned, add None placeholders
                        features.extend([None] * len(batch))
                except Exception as batch_error:
                    error_str = str(batch_error).lower()
                    if "403" in error_str or "forbidden" in error_str:
                        logger.warning(
                            "Audio features API returned 403 for batch. "
                            "Client Credentials may not have access."
                        )
                        raise  # Re-raise to be handled by caller
                    elif "429" in error_str or "rate limit" in error_str:
                        logger.warning("Rate limit hit, waiting...")
                        # Could add retry logic here
                        raise
                    else:
                        logger.warning(
                            f"Failed to get features for batch: {batch_error}"
                        )
                        # Add None placeholders for failed batch
                        features.extend([None] * len(batch))

            return features

        except Exception as e:
            logger.error(f"Failed to get audio features: {e}")
            raise

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
        Отримати seed tracks з жанрів.

        Args:
            genres: Список жанрів
            limit_per_genre: Кількість треків на жанр
            user_token: User access token (опціонально)

        Returns:
            Список track IDs для використання як seeds
        """
        seed_tracks = []
        genres = genres[:2] if genres else []

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
        }

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
                logger.warning(f"Failed to get seed tracks for {genre}: {e}")
                continue

        return seed_tracks[:5]  # Max 5 seeds

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

            # Strategy 1: Prompt-based search
            if search_query and search_query.strip():
                prompt_clean = search_query.strip()[:100]
                search_queries.append(prompt_clean)

            # Strategy 2: Genre-based search
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

            for genre in genres:
                search_term = genre_map.get(genre.lower(), genre)
                search_queries.append(search_term)

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
                    found_tracks = search_results.get("tracks", {}).get("items", [])

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

            # Final fallback
            if not all_tracks:
                try:
                    search_results = sp.search(
                        q="workout music OR running music",
                        type="track",
                        limit=limit,
                        market="US"
                    )
                    all_tracks = search_results.get("tracks", {}).get("items", [])
                except Exception as e:
                    logger.error(f"Final fallback search failed: {e}")
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

                if (min_tempo <= tempo <= max_tempo and
                        energy >= target_energy * 0.8):
                    track.update(features[i])
                    filtered_tracks.append(track)
                    if len(filtered_tracks) >= limit:
                        break

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
        Оптимізований batch запит для audio features.

        Spotify API дозволяє до 100 треків в одному запиті.
        """
        if not track_ids:
            return []

        features = []
        batch_size = min(batch_size, 100)  # Spotify limit

        # Використовуємо User Auth якщо доступний
        if user_token:
            sp = spotipy.Spotify(auth=user_token)
        else:
            sp = spotipy.Spotify(
                client_credentials_manager=self.client_credentials
            )

        # Розбиваємо на батчі
        for i in range(0, len(track_ids), batch_size):
            batch = track_ids[i:i + batch_size]

            try:
                batch_features = sp.audio_features(batch)
                if batch_features:
                    features.extend(batch_features)
                else:
                    features.extend([None] * len(batch))
            except Exception as e:
                error_str = str(e).lower()
                if "403" in error_str or "forbidden" in error_str:
                    logger.warning(
                        f"Audio features API returned 403 for batch {i//batch_size}. "
                        "This may indicate insufficient permissions."
                    )
                else:
                    logger.warning(f"Batch {i//batch_size} failed: {e}")
                features.extend([None] * len(batch))

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
