"""
Spotify Service for API integration.
"""
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from app.core.config import settings
from loguru import logger
from typing import List, Dict, Optional
import asyncio


class SpotifyService:
    """Service for Spotify API operations."""

    def __init__(self):
        """Initialize Spotify client credentials."""
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
                    client_credentials_manager=self.client_credentials)
            except Exception as auth_error:
                logger.error(f"Failed to create Spotify client: {auth_error}")
                raise

            # Spotify API requires at least one seed (genre or artist)
            # Must have at least 1 seed, max 5 total seeds
            seed_genres_list = list(seed_genres[:2]) if seed_genres else []
            seed_artists_list = list(seed_artists[:2]) if seed_artists else []

            # If no seeds provided, use default genres
            if not seed_genres_list and not seed_artists_list:
                seed_genres_list = ["pop", "rock"]

            # Build recommendations parameters
            # Start with minimal required parameters
            rec_params = {
                "limit": limit,
                "target_energy": target_energy,
            }

            # Add tempo parameters - Spotify API may have issues with all three together
            # Try using just min/max_tempo first, as they define a range
            rec_params["min_tempo"] = min_tempo
            rec_params["max_tempo"] = max_tempo

            # Only add target_tempo if it's within the range and different from midpoint
            midpoint = (min_tempo + max_tempo) / 2
            if abs(target_tempo - midpoint) > 5:  # Only if significantly different
                rec_params["target_tempo"] = target_tempo

            # Add seeds (at least one required)
            # spotipy expects lists, not strings
            if seed_genres_list:
                rec_params["seed_genres"] = seed_genres_list
            if seed_artists_list:
                rec_params["seed_artists"] = seed_artists_list

            logger.debug(f"Spotify recommendations params: {rec_params}")

            # Try the request with full parameters first
            results = None
            last_error = None

            try:
                results = sp.recommendations(**rec_params)
            except Exception as spotify_error:
                last_error = spotify_error
                error_str = str(spotify_error).lower()

                # If 404 or parameter error, try simplified parameters
                if "404" in error_str or "not found" in error_str or "parameter" in error_str:
                    logger.warning(
                        f"Recommendations failed with full params, trying simplified: {spotify_error}"
                    )

                    # Try without target_tempo
                    if "target_tempo" in rec_params:
                        rec_params_simple = rec_params.copy()
                        rec_params_simple.pop("target_tempo", None)
                        logger.debug(
                            f"Retry params (no target_tempo): {rec_params_simple}")
                        try:
                            results = sp.recommendations(**rec_params_simple)
                        except Exception as e2:
                            last_error = e2
                            # Try with just seeds and energy
                            rec_params_minimal = {
                                "limit": limit,
                                "target_energy": target_energy,
                            }
                            if seed_genres_list:
                                rec_params_minimal["seed_genres"] = seed_genres_list
                            if seed_artists_list:
                                rec_params_minimal["seed_artists"] = seed_artists_list
                            logger.debug(
                                f"Retry params (minimal): {rec_params_minimal}")
                            results = sp.recommendations(**rec_params_minimal)
                else:
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
