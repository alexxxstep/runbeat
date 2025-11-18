"""
Spotify Recommendation related methods.
"""

from typing import Dict, List, Optional
import spotipy
from loguru import logger
import time  # Import time for TTL check


class RecommendationsMixin:
    """Methods for getting track recommendations."""

    async def get_recommendations(
        self,
        seed_genres: List[str],
        seed_artists: List[str],
        target_tempo: int,
        min_tempo: int,
        max_tempo: int,
        target_energy: float,
        limit: int = 20,
        user_token: Optional[str] = None,
    ) -> List[Dict]:
        """
        Get track recommendations from Spotify, with caching support.
        """
        # --- OPTIMIZATION: Caching ---
        cache_key = self._get_cache_key(seed_genres, min_tempo, max_tempo, target_energy)
        if cache_key in self._cache:
            cached_data, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self._cache_ttl:
                logger.debug(f"Cache hit for recommendations key: {cache_key}")
                return cached_data[:limit]
        # --- END OPTIMIZATION ---

        try:
            # Use user-specific client if token is provided
            if user_token:
                sp = self.get_user_client(user_token)
                logger.debug("Using user-specific Spotify client for recommendations.")
            else:
                sp = spotipy.Spotify(client_credentials_manager=self.client_credentials)
                logger.debug("Using client credentials for recommendations.")

            # Test authentication
            try:
                if not user_token:
                    token_info = self.client_credentials.get_access_token(as_dict=False)
                    if not token_info:
                        raise Exception("Spotify authentication failed: no access token received")
                logger.debug("Spotify access token obtained successfully")
            except Exception as token_error:
                logger.error(f"Failed to get Spotify access token: {token_error}")
                raise Exception(f"Spotify authentication failed: {token_error}")

            seed_genres_list = list(seed_genres[:2]) if seed_genres else []
            seed_artists_list = list(seed_artists[:2]) if seed_artists else []
            seed_tracks_list = []

            logger.debug(
                f"Attempting to get seed tracks (genres: {seed_genres_list}, artists: {seed_artists_list})"
            )
            try:
                if seed_genres_list and len(seed_tracks_list) < 5:
                    try:
                        seed_tracks_list = await self.get_seed_tracks_from_genres(
                            seed_genres_list, limit_per_genre=3, user_token=None
                        )
                        if seed_tracks_list:
                            logger.debug(
                                f"Got {len(seed_tracks_list)} seed tracks from optimized method"
                            )
                    except Exception as optimized_error:
                        logger.debug(
                            f"Optimized seed tracks method failed: {optimized_error}, using fallback"
                        )
                        # Fallback to sequential search
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
                                search_term = genre_map.get(genre.lower(), genre)
                                search_results = sp.search(
                                    q=search_term, type="track", limit=5, market="US"
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
                                logger.debug(
                                    f"Genre search for {genre} failed: {genre_search_error}"
                                )
                                continue

                if not seed_tracks_list:
                    if not seed_genres_list:
                        seed_genres_list = ["pop", "rock"]
                    logger.debug("Using genres as seeds (no tracks found)")

            except Exception as general_error:
                logger.warning(
                    f"Failed to get seed tracks: {general_error}. Using genres as fallback"
                )
                if not seed_genres_list:
                    seed_genres_list = ["pop", "rock"]

            rec_params = {
                "limit": limit,
                "target_energy": target_energy,
                "min_tempo": min_tempo,
                "max_tempo": max_tempo,
            }

            if seed_tracks_list:
                rec_params["seed_tracks"] = seed_tracks_list[:5]
                logger.debug(f"Using {len(seed_tracks_list)} track seeds")
            else:
                if seed_genres_list:
                    rec_params["seed_genres"] = seed_genres_list
                if seed_artists_list:
                    rec_params["seed_artists"] = seed_artists_list

            logger.debug(f"Spotify recommendations params: {rec_params}")

            results = None
            last_error = None

            try:
                logger.debug(f"Attempting recommendations with params: {rec_params}")
                results = sp.recommendations(**rec_params)
                logger.debug("Recommendations request successful")
            except Exception as spotify_error:
                last_error = spotify_error
                error_str = str(spotify_error).lower()
                logger.warning(f"Recommendations failed: {spotify_error}")

                # Check for 403 Forbidden error (Development Mode)
                is_403_error = "403" in error_str or "http status: 403" in error_str
                status_code = getattr(spotify_error, "http_status", None) or getattr(
                    spotify_error, "code", None
                )
                if status_code == 403:
                    is_403_error = True

                if is_403_error:
                    logger.error(
                        "403 Forbidden - Spotify app is in Development Mode. "
                        "Please switch to Extended Quota Mode on developer.spotify.com/dashboard"
                    )
                    raise Exception(
                        "Spotify API недоступний. Додаток знаходиться в режимі розробки. "
                        "Будь ласка, зверніться до адміністратора для активації Extended Quota Mode."
                    )

                is_404_error = (
                    "404" in error_str
                    or "not found" in error_str
                    or "http status: 404" in error_str
                )
                if status_code == 404:
                    is_404_error = True

                if is_404_error:
                    logger.error(
                        "404 error - Recommendations API not available. Falling back to Search API."
                    )
                    return await self.get_tracks_by_search(
                        seed_genres=seed_genres_list,
                        min_tempo=min_tempo,
                        max_tempo=max_tempo,
                        target_energy=target_energy,
                        limit=limit,
                    )
                else:
                    logger.warning(
                        f"Unknown error type: {error_str[:100]}. Trying Search API as fallback"
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
                        logger.error(f"Search API fallback failed: {search_error}")
                        raise Exception(
                            f"Spotify API request failed. Recs API error: {last_error}. Search API fallback also failed: {search_error}"
                        )

            if results is None:
                logger.error("All recommendation attempts failed")
                if last_error:
                    raise last_error
                raise Exception("Failed to get recommendations from Spotify")

            tracks = results.get("tracks", [])
            if not tracks:
                logger.warning("No tracks returned from Spotify recommendations")
                return []

            track_ids = [track["id"] for track in tracks]
            features = await self.get_audio_features_batch_optimized(
                track_ids=track_ids, batch_size=100, user_token=None
            )

            for i, track in enumerate(tracks):
                if i < len(features) and features[i]:
                    track.update(features[i])

            if features and sum(1 for f in features if f) > len(features) * 0.5:
                # Cache the successful result before returning
                self._cache[cache_key] = (tracks, time.time())

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
        **kwargs,
    ) -> List[Dict]:
        """
        Get track recommendations from Spotify with advanced filters.
        """
        try:
            sp = spotipy.Spotify(client_credentials_manager=self.client_credentials)

            rec_params = {
                "limit": min(limit, 100),
                "market": market,
            }

            # Seed handling
            seed_artists_list = list(seed_artists) if seed_artists else []
            seed_tracks_list = list(seed_tracks) if seed_tracks else []
            seed_genres_list = list(seed_genres) if seed_genres else []

            total_seeds = len(seed_artists_list) + len(seed_tracks_list) + len(seed_genres_list)
            if total_seeds > 5:
                logger.warning(f"Too many seeds ({total_seeds}), trimming to 5")
                # Simple trim, can be made proportional
                seed_artists_list = seed_artists_list[:2]
                seed_tracks_list = seed_tracks_list[:2]
                seed_genres_list = seed_genres_list[:1]

            if not any([seed_artists_list, seed_tracks_list, seed_genres_list]):
                raise ValueError("At least one seed (artist, track, or genre) must be provided.")

            if seed_tracks_list:
                rec_params["seed_tracks"] = seed_tracks_list
            if seed_artists_list:
                rec_params["seed_artists"] = seed_artists_list
            if seed_genres_list:
                rec_params["seed_genres"] = seed_genres_list

            # Add all other kwargs as filters
            rec_params.update(kwargs)

            logger.debug(f"Spotify advanced recommendations params: {rec_params}")

            try:
                results = sp.recommendations(**rec_params)
            except Exception as spotify_error:
                logger.error(f"Advanced recommendations failed: {spotify_error}")
                raise

            tracks = results.get("tracks", [])
            if not tracks:
                logger.warning("No tracks returned from advanced recommendations.")
                return []

            track_ids = [track["id"] for track in tracks if track.get("id")]
            features = await self.get_audio_features_batch_optimized(
                track_ids=track_ids, batch_size=100
            )

            for i, track in enumerate(tracks):
                if i < len(features) and features[i]:
                    track.update(features[i])

            return tracks

        except Exception as e:
            logger.error(f"Failed to get advanced recommendations: {e}")
            raise
