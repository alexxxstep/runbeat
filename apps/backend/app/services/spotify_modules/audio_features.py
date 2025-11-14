"""
Spotify Audio Features related methods.
"""
import asyncio
import time
from typing import Dict, List, Optional
import spotipy
from loguru import logger


class AudioFeaturesMixin:
    """Methods for fetching audio features for tracks."""

    async def get_audio_features_batch(
        self,
        track_ids: List[str],
    ) -> List[Optional[Dict]]:
        """
        Get audio features for multiple tracks (batch).
        This is a wrapper around the optimized version.
        """
        return await self.get_audio_features_batch_optimized(
            track_ids=track_ids,
            batch_size=100,
            user_token=None
        )

    async def get_audio_features_batch_optimized(
        self,
        track_ids: List[str],
        batch_size: int = 100,
        user_token: Optional[str] = None
    ) -> List[Optional[Dict]]:
        """
        Optimized batch request for audio features with parallel execution.
        """
        if not track_ids:
            return []

        batch_size = min(batch_size, 100)  # Spotify limit
        cache_key = f"audio_features_{hash(tuple(track_ids[:50]))}"

        if cache_key in self._cache:
            cached_data, timestamp = self._cache[cache_key]
            if time.time() - timestamp < 3600:
                logger.debug(f"Cache hit for audio features: {len(track_ids)} tracks")
                return cached_data

        sp = spotipy.Spotify(auth=user_token) if user_token else spotipy.Spotify(
            client_credentials_manager=self.client_credentials
        )

        async def fetch_batch(batch: List[str], batch_num: int) -> List[Optional[Dict]]:
            try:
                loop = asyncio.get_event_loop()
                batch_features = await loop.run_in_executor(
                    None,
                    lambda: sp.audio_features(batch)
                )
                return batch_features or [None] * len(batch)
            except Exception as e:
                # Handle specific errors like 403, 429
                logger.warning(f"Audio features batch {batch_num} failed: {e}")
                return [None] * len(batch)

        batches = [track_ids[i:i + batch_size] for i in range(0, len(track_ids), batch_size)]

        try:
            semaphore = asyncio.Semaphore(3)
            async def fetch_with_semaphore(batch: List[str], batch_num: int):
                async with semaphore:
                    return await fetch_batch(batch, batch_num)

            results = await asyncio.gather(*(fetch_with_semaphore(b, i) for i, b in enumerate(batches)))

            features = [item for sublist in results for item in sublist]
        except Exception as e:
            logger.warning(f"Parallel audio features fetch failed: {e}, falling back to sequential.")
            # Sequential fallback
            features = []
            for i, batch in enumerate(batches):
                features.extend(await fetch_batch(batch, i))

        if features and all(f is None for f in features):
            logger.warning("All audio features were None, likely a permission issue.")
            return []

        if features and sum(1 for f in features if f) > len(features) * 0.5:
            self._cache[cache_key] = (features, time.time())

        return features
