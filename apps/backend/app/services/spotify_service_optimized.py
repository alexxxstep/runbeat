"""
Оптимізований Spotify Service з покращеною стратегією запитів.

Основні покращення:
1. Використання User Authorization для Recommendations API
2. Batch запити для audio features
3. Кешування результатів
4. Оптимізована fallback стратегія
"""
from typing import Dict, List, Optional
import time
import hashlib
import json
import asyncio

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from app.core.config import settings
from loguru import logger


class OptimizedSpotifyService:
    """
    Оптимізований Spotify Service з покращеною продуктивністю.
    """

    def __init__(self):
        """Initialize Spotify client credentials."""
        if (not settings.SPOTIFY_CLIENT_ID or
                not settings.SPOTIFY_CLIENT_SECRET):
            logger.error("Spotify credentials are missing!")
            raise ValueError(
                "SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET must be set"
            )

        self.client_credentials = SpotifyClientCredentials(
            client_id=settings.SPOTIFY_CLIENT_ID,
            client_secret=settings.SPOTIFY_CLIENT_SECRET,
        )

        # In-memory cache
        self._cache = {}
        self._cache_ttl = 3600  # 1 hour

        logger.info("OptimizedSpotifyService initialized")

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

        Args:
            seed_genres: Список жанрів
            seed_artists: Список artist IDs
            target_tempo: Цільовий BPM
            min_tempo: Мінімальний BPM
            max_tempo: Максимальний BPM
            target_energy: Цільова енергія (0-1)
            limit: Кількість рекомендацій
            user_token: User access token (опціонально)
            use_cache: Використовувати кеш

        Returns:
            Список треків з audio features
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
                    # Використовувати seed_tracks (більш надійно)
                    rec_params = {
                        "seed_tracks": seed_tracks[:5],
                        "min_tempo": min_tempo,
                        "max_tempo": max_tempo,
                        "target_energy": target_energy,
                        "limit": limit
                    }
                else:
                    # Fallback до seed_genres
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

            # Final fallback
            if not all_tracks:
                try:
                    search_results = sp.search(
                        q="workout music OR running music",
                        type="track",
                        limit=limit,
                        market="US"
                    )
                    all_tracks = search_results.get(
                        "tracks", {}).get("items", [])
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
                        # Default values
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
        Це значно зменшує кількість запитів.

        Args:
            track_ids: Список track IDs
            batch_size: Розмір батчу (max 100)
            user_token: User access token (опціонально)

        Returns:
            Список audio features (може містити None для помилок)
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
                    logger.warning(
                        f"Batch {i//batch_size} failed: {e}"
                    )
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
            "cached_keys": list(self._cache.keys())[:10]  # First 10 keys
        }
