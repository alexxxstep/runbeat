"""
Spotify User Profile related methods.
"""
from typing import Dict, List
import spotipy
from loguru import logger


class UserProfileMixin:
    """Methods for fetching user-specific data like top tracks and artists."""

    async def get_user_top_tracks(
        self,
        user_client: spotipy.Spotify,
        limit: int = 50,
    ) -> List[Dict]:
        """
        Get user's top tracks.
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
        """
        try:
            results = user_client.current_user_top_artists(
                limit=limit, time_range="medium_term"
            )
            return results.get("items", [])
        except Exception as e:
            logger.error(f"Failed to get user top artists: {e}")
            raise
