"""
Spotify Service for API integration.
"""
from typing import Dict, List, Optional

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

            # Build search query from genres
            genres = seed_genres[:2] if seed_genres else ["pop", "rock"]
            query_parts = [f"genre:{g}" for g in genres]
            query = " OR ".join(query_parts)

            logger.debug(f"Searching tracks with query: {query}")

            # Search for tracks (get more than limit to filter)
            search_results = sp.search(
                q=query,
                type="track",
                limit=min(50, limit * 3),  # Get more to filter
                market="US"
            )

            tracks = search_results.get("tracks", {}).get("items", [])

            if not tracks:
                logger.warning("No tracks found in search")
                return []

            # Get track IDs
            track_ids = [t["id"] for t in tracks if t.get("id")]

            if not track_ids:
                logger.warning("No valid track IDs found")
                return []

            # Get audio features for all tracks
            features_list = await self.get_audio_features_batch(track_ids)

            # Filter tracks by tempo and energy
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

            # If no seeds provided, get popular tracks to use as seeds
            # This is a workaround for Client Credentials limitations
            # seed_tracks are more reliable than seed_genres
            # with Client Credentials
            if not seed_genres_list and not seed_artists_list:
                logger.debug(
                    "No seeds provided, fetching popular tracks for seeds"
                )
                try:
                    # Method 1: Try to get tracks from featured playlists
                    try:
                        featured = sp.featured_playlists(limit=1)
                        playlists = featured.get("playlists", {}).get(
                            "items", []
                        )
                        if playlists:
                            playlist_id = playlists[0]["id"]
                            playlist_tracks = sp.playlist_tracks(
                                playlist_id, limit=5
                            )
                            tracks = [
                                item["track"]
                                for item in playlist_tracks.get("items", [])
                                if (item.get("track") and
                                    item["track"].get("id"))
                            ]
                            seed_tracks_list = [t["id"] for t in tracks[:5]]
                            if seed_tracks_list:
                                logger.debug(
                                    f"Found {len(seed_tracks_list)} tracks "
                                    "from featured playlist"
                                )
                    except Exception as playlist_error:
                        logger.debug(
                            f"Featured playlists failed: {playlist_error}"
                        )
                        # Method 2: Search for popular tracks
                        try:
                            search_results = sp.search(
                                q="year:2023 OR year:2024",
                                type="track",
                                limit=5,
                                market="US"
                            )
                            tracks = search_results.get("tracks", {}).get(
                                "items", []
                            )
                            seed_tracks_list = [
                                t["id"] for t in tracks[:5] if t.get("id")
                            ]
                            if seed_tracks_list:
                                logger.debug(
                                    f"Found {len(seed_tracks_list)} tracks "
                                    "from search"
                                )
                        except Exception as search_error:
                            logger.warning(
                                f"Search also failed: {search_error}"
                            )

                    # Fallback to genres if all methods fail
                    if not seed_tracks_list:
                        seed_genres_list = ["pop", "rock"]
                        logger.debug("Using default genres as fallback")
                except Exception as general_error:
                    logger.warning(
                        f"Failed to get seed tracks: {general_error}. "
                        "Using default genres"
                    )
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
        """
        try:
            sp = spotipy.Spotify(
                client_credentials_manager=self.client_credentials)

            # Spotify API allows max 100 tracks per request
            features = []
            for i in range(0, len(track_ids), 100):
                batch = track_ids[i: i + 100]
                batch_features = sp.audio_features(batch)
                features.extend(batch_features)

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
