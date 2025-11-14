"""
Spotify Search related methods.
"""
import asyncio
from typing import Dict, List, Optional
import spotipy
from loguru import logger


class SearchMixin:
    """Methods for searching tracks, artists, etc."""

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
        Get tracks using Search API with parallel execution.
        This method acts as a fallback when the Recommendations API fails.
        It searches for tracks across multiple queries and filters by audio features.
        """
        try:
            sp = spotipy.Spotify(
                client_credentials_manager=self.client_credentials
            )

            # Build a list of diverse search queries
            search_queries = self._build_search_queries(seed_genres, search_query)

            # --- OPTIMIZATION: Parallel Search Execution ---
            loop = asyncio.get_event_loop()
            
            async def search_task(query: str):
                try:
                    logger.debug(f"Executing search query: '{query}'")
                    return await loop.run_in_executor(
                        None,  # Use default thread pool
                        lambda: sp.search(q=query, type="track", limit=50, market="US")
                    )
                except Exception as e:
                    logger.warning(f"Search query '{query}' failed: {e}")
                    return None

            # Execute all search tasks concurrently
            search_results_list = await asyncio.gather(*(search_task(q) for q in search_queries))
            
            # Process results: collect unique tracks
            all_tracks = {} # Use dict to handle duplicates automatically
            for results in search_results_list:
                if results:
                    found_tracks = results.get("tracks", {}).get("items", [])
                    for track in found_tracks:
                        if track and track.get("id"):
                            all_tracks[track["id"]] = track
            
            tracks = list(all_tracks.values())
            logger.debug(f"Found a total of {len(tracks)} unique tracks from parallel search.")
            # --- END OPTIMIZATION ---

            if not tracks:
                logger.warning("No tracks found from any parallel search query.")
                return []

            # Get track IDs for audio features batch request
            track_ids = [t["id"] for t in tracks if t.get("id")]
            if not track_ids:
                logger.warning("No valid track IDs to fetch audio features for.")
                return []

            # Fetch audio features in a batch
            features_list = await self.get_audio_features_batch(track_ids)

            # Merge tracks with their audio features
            tracks_with_features = []
            features_map = {f["id"]: f for f in features_list if f and f.get("id")}
            
            for track in tracks:
                if track["id"] in features_map:
                    track.update(features_map[track["id"]])
                    tracks_with_features.append(track)
            
            # Filter tracks based on tempo and energy criteria
            min_energy = max(0.6, target_energy * 0.8)
            filtered_tracks = [
                t for t in tracks_with_features
                if t.get("tempo") and min_tempo <= t["tempo"] <= max_tempo and
                   t.get("energy", 0) >= min_energy
            ]

            # Sort by energy to prioritize more dynamic tracks
            filtered_tracks.sort(key=lambda x: x.get("energy", 0), reverse=True)
            
            logger.info(f"Found {len(filtered_tracks)} tracks matching criteria from {len(tracks)} unique results.")
            
            # If filtering returns too few tracks, return the best unfiltered ones
            if not filtered_tracks:
                logger.warning("No tracks matched filtering criteria. Returning top unfiltered results.")
                # Return original tracks with placeholder features if needed
                unfiltered_with_defaults = []
                for track in tracks[:limit]:
                    if track["id"] not in features_map:
                         track.update({
                            "tempo": (min_tempo + max_tempo) / 2, "energy": target_energy,
                            "danceability": 0.7, "valence": 0.7,
                        })
                    unfiltered_with_defaults.append(track)
                return unfiltered_with_defaults

            return filtered_tracks[:limit]

        except Exception as e:
            logger.error(f"Failed to get tracks by parallel search: {e}")
            raise
    
    def _build_search_queries(self, seed_genres: List[str], search_query: Optional[str]) -> List[str]:
        """Helper method to construct a list of search queries."""
        genres = seed_genres[:2] if seed_genres else ["pop", "rock"]
        search_queries = []

        genre_map = {
            "pop": "pop music", "rock": "rock music", "electronic": "electronic music",
            "hip-hop": "hip hop", "r&b": "r&b music", "country": "country music",
            "jazz": "jazz music", "classical": "classical music", "reggae": "reggae music",
            "metal": "metal music", "indie": "indie music", "alternative": "alternative music",
            "dance": "dance music", "house": "house music", "techno": "techno music",
            "edm": "edm music", "trance": "trance music",
        }

        for genre in genres:
            genre_term = genre_map.get(genre.lower(), genre)
            search_queries.extend([
                f"{genre_term} workout", f"{genre_term} fitness",
                f"{genre_term} energetic", f"{genre_term} upbeat", f"{genre_term} running"
            ])

        if search_query and search_query.strip():
            prompt_clean = search_query.strip()[:80]
            search_queries.insert(0, f"{prompt_clean} workout")
            search_queries.insert(1, f"{prompt_clean} fitness")
            search_queries.insert(2, prompt_clean)

        if not search_queries or len(search_queries) < 5:
            search_queries.extend([
                "workout music", "fitness music", "gym music", "running music",
                "energetic music", "upbeat workout", "dynamic fitness", "motivational workout",
                "workout music energetic", "fitness music upbeat", "gym music dynamic",
                "running music motivational", "cardio workout music", "high energy workout"
            ])
        
        return list(dict.fromkeys(search_queries)) # Return unique queries
    
    async def search_track_by_name(
        self,
        track_name: str,
        artist_name: Optional[str] = None,
        limit: int = 1,
    ) -> Optional[Dict]:
        """
        Search for a specific track by name and optionally artist.
        """
        try:
            sp = spotipy.Spotify(
                client_credentials_manager=self.client_credentials
            )

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
