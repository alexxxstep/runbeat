"""
Playlist Generator - Core algorithm for generating workout playlists.
"""
from typing import List, Dict
from app.models.workout import Workout
from app.models.playlist import Track, PlaylistData
from app.services.spotify_service import SpotifyService
from loguru import logger
import asyncio


class PlaylistGenerator:
    """
    Single-class playlist generator (simplified from 7 agents).
    Generates personalized workout playlists based on workout parameters.
    """

    def __init__(self, spotify: SpotifyService):
        """
        Initialize playlist generator.

        Args:
            spotify: SpotifyService instance
        """
        self.spotify = spotify

    async def generate(
        self,
        workout: Workout,
        user_preferences: Dict,
    ) -> PlaylistData:
        """
        Main generation method.

        Args:
            workout: Workout parameters
            user_preferences: User preferences (genres, artists, etc.)

        Returns:
            PlaylistData with selected tracks
        """
        logger.info(
            f"Generating playlist for {workout.type} workout, {workout.duration_minutes} min"
        )

        # 1. Create workout segments
        segments = self._create_segments(workout)
        logger.debug(f"Created {len(segments)} segments")

        # 2. Fetch candidate tracks (parallel)
        candidates = await self._fetch_candidates(segments, user_preferences)
        logger.debug(f"Fetched {len(candidates)} candidate tracks")

        # 3. Score tracks
        scored = self._score_tracks(candidates, segments, user_preferences)
        logger.debug(f"Scored {len(scored)} tracks")

        # 4. Optimize selection
        selected = self._optimize_selection(
            scored, workout.duration_minutes * 60)
        logger.info(f"Selected {len(selected)} tracks for playlist")

        total_duration = sum(t.duration_ms for t in selected) / 1000

        return PlaylistData(
            tracks=selected,
            total_duration=total_duration,
            total_tracks=len(selected),
        )

    def _create_segments(self, workout: Workout) -> List[Dict]:
        """
        Create workout segments with BPM ranges.

        Args:
            workout: Workout parameters

        Returns:
            List of segment dictionaries with BPM ranges
        """
        if workout.type == "steady":
            target_bpm = self._calculate_target_bpm(workout.intensity)
            return [
                {
                    "name": "warm-up",
                    "duration": 5,
                    "bpm_range": [target_bpm - 20, target_bpm - 10],
                },
                {
                    "name": "main",
                    "duration": max(5, workout.duration_minutes - 10),
                    "bpm_range": [target_bpm - 5, target_bpm + 5],
                },
                {
                    "name": "cool-down",
                    "duration": 5,
                    "bpm_range": [target_bpm - 25, target_bpm - 15],
                },
            ]

        elif workout.type == "progressive":
            start_bpm = self._calculate_target_bpm("low")
            end_bpm = self._calculate_target_bpm("high")
            num_segments = 5

            segments = []
            for i in range(num_segments):
                progress = i / (num_segments - 1)
                current_bpm = start_bpm + (end_bpm - start_bpm) * progress
                segments.append(
                    {
                        "name": f"segment_{i+1}",
                        "duration": workout.duration_minutes / num_segments,
                        "bpm_range": [current_bpm - 5, current_bpm + 5],
                    }
                )
            return segments

        elif workout.type == "intervals":
            # Intervals: alternate between work and rest segments
            target_bpm = self._calculate_target_bpm(workout.intensity)
            # Simplified: assume equal work/rest ratio
            segment_duration = workout.duration_minutes / 8  # 4 work + 4 rest
            segments = []
            for i in range(8):
                if i % 2 == 0:  # Work segment
                    segments.append(
                        {
                            "name": f"work_{i//2 + 1}",
                            "duration": segment_duration,
                            "bpm_range": [target_bpm - 5, target_bpm + 10],
                        }
                    )
                else:  # Rest segment
                    segments.append(
                        {
                            "name": f"rest_{i//2 + 1}",
                            "duration": segment_duration,
                            "bpm_range": [target_bpm - 30, target_bpm - 20],
                        }
                    )
            return segments

        elif workout.type == "fartlek":
            # Fartlek: varied pace segments
            target_bpm = self._calculate_target_bpm(workout.intensity)
            num_segments = 6
            segment_duration = workout.duration_minutes / num_segments
            segments = []
            for i in range(num_segments):
                # Alternate between moderate and high intensity
                if i % 2 == 0:
                    bpm_range = [target_bpm - 10, target_bpm + 5]
                else:
                    bpm_range = [target_bpm + 5, target_bpm + 20]
                segments.append(
                    {
                        "name": f"fartlek_{i+1}",
                        "duration": segment_duration,
                        "bpm_range": bpm_range,
                    }
                )
            return segments

        return []

    def _calculate_target_bpm(self, intensity: str) -> int:
        """
        Calculate target BPM from intensity.

        Args:
            intensity: Workout intensity (low, moderate, high)

        Returns:
            Target BPM value
        """
        intensity_map = {
            "low": 125,  # Easy pace
            "moderate": 145,  # Tempo pace
            "high": 165,  # Fast pace
        }
        return intensity_map.get(intensity, 145)

    async def _fetch_candidates(
        self, segments: List[Dict], user_prefs: Dict
    ) -> List[Track]:
        """
        Fetch candidate tracks for all segments (parallel).

        Args:
            segments: List of workout segments
            user_prefs: User preferences

        Returns:
            List of Track objects
        """
        tasks = [self._fetch_for_segment(seg, user_prefs) for seg in segments]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_candidates = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error fetching segment tracks: {result}")
                continue
            all_candidates.extend(result)

        return all_candidates

    async def _fetch_for_segment(
        self, segment: Dict, user_prefs: Dict
    ) -> List[Track]:
        """
        Fetch tracks for one segment.

        Args:
            segment: Segment dictionary with BPM range
            user_prefs: User preferences

        Returns:
            List of Track objects
        """
        bpm_min, bpm_max = segment["bpm_range"]
        target_bpm = int((bpm_min + bpm_max) / 2)

        # Use Spotify Recommendations API
        spotify_tracks = await self.spotify.get_recommendations(
            seed_genres=user_prefs.get("top_genres", [])[:2],
            seed_artists=user_prefs.get("top_artists", [])[:2],
            target_tempo=target_bpm,
            min_tempo=int(bpm_min),
            max_tempo=int(bpm_max),
            target_energy=0.7,  # High energy for workouts
            limit=20,
        )

        # Convert Spotify tracks to Track models
        tracks = []
        for spotify_track in spotify_tracks:
            try:
                track = self._spotify_to_track(spotify_track)
                if track:
                    tracks.append(track)
            except Exception as e:
                logger.warning(f"Failed to convert track: {e}")
                continue

        return tracks

    def _spotify_to_track(self, spotify_track: Dict) -> Track:
        """
        Convert Spotify track dictionary to Track model.

        Args:
            spotify_track: Spotify API track dictionary

        Returns:
            Track model instance
        """
        # Extract basic info
        track_id = spotify_track.get("id", "")
        name = spotify_track.get("name", "Unknown")
        artists = spotify_track.get("artists", [])
        artist = artists[0].get("name", "Unknown") if artists else "Unknown"
        artist_id = artists[0].get("id", "") if artists else ""
        album = spotify_track.get("album", {}).get("name", "")
        duration_ms = spotify_track.get("duration_ms", 0)
        spotify_url = spotify_track.get("external_urls", {}).get("spotify", "")
        spotify_uri = spotify_track.get("uri", "")
        preview_url = spotify_track.get("preview_url")

        # Extract audio features
        tempo = spotify_track.get("tempo", 120.0)
        energy = spotify_track.get("energy", 0.5)
        danceability = spotify_track.get("danceability", 0.5)
        valence = spotify_track.get("valence", 0.5)

        # Extract genres from album or artist (if available)
        genres = []
        if "album" in spotify_track and "genres" in spotify_track["album"]:
            genres = spotify_track["album"]["genres"]
        elif artists and "genres" in artists[0]:
            genres = artists[0].get("genres", [])

        return Track(
            id=track_id,
            name=name,
            artist=artist,
            artist_id=artist_id,
            album=album,
            duration_ms=duration_ms,
            spotify_url=spotify_url,
            spotify_uri=spotify_uri,
            preview_url=preview_url,
            tempo=tempo,
            bpm=tempo,
            energy=energy,
            danceability=danceability,
            valence=valence,
            genres=genres,
        )

    def _score_tracks(
        self,
        candidates: List[Track],
        segments: List[Dict],
        user_prefs: Dict,
    ) -> List[Dict]:
        """
        Score tracks based on BPM, energy, user affinity.

        Args:
            candidates: List of candidate tracks
            segments: List of workout segments
            user_prefs: User preferences

        Returns:
            List of scored track dictionaries
        """
        scored = []

        for track in candidates:
            # Find best matching segment
            best_segment = min(
                segments,
                key=lambda s: abs(
                    (s["bpm_range"][0] + s["bpm_range"][1]) / 2 - track.bpm
                ),
            )

            # Calculate scores
            bpm_score = self._bpm_match_score(
                track.bpm, best_segment["bpm_range"])
            energy_score = track.energy  # Already 0-1
            affinity_score = self._calculate_affinity(track, user_prefs)

            # Weighted total
            total = bpm_score * 0.40 + energy_score * 0.25 + affinity_score * 0.35

            scored.append(
                {
                    "track": track,
                    "score": total,
                    "segment": best_segment["name"],
                }
            )

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored

    def _bpm_match_score(self, bpm: float, bpm_range: List[int]) -> float:
        """
        Calculate BPM match score (0-1).

        Args:
            bpm: Track BPM
            bpm_range: Target BPM range [min, max]

        Returns:
            Score between 0 and 1
        """
        min_bpm, max_bpm = bpm_range
        if min_bpm <= bpm <= max_bpm:
            return 1.0
        # Penalty for out of range
        distance = min(abs(bpm - min_bpm), abs(bpm - max_bpm))
        return max(0, 1 - distance / 20)  # 20 BPM tolerance

    def _calculate_affinity(self, track: Track, user_prefs: Dict) -> float:
        """
        Calculate user affinity score (0-1).

        Args:
            track: Track object
            user_prefs: User preferences

        Returns:
            Affinity score between 0 and 1
        """
        score = 0.5  # Base score

        # Genre match
        user_genres = user_prefs.get("top_genres", [])
        if user_genres and any(g in user_genres for g in track.genres):
            score += 0.3

        # Artist match
        user_artists = user_prefs.get("top_artists", [])
        if user_artists and track.artist_id in user_artists:
            score += 0.2

        return min(1.0, score)

    def _optimize_selection(
        self,
        scored_tracks: List[Dict],
        target_duration: int,  # seconds
    ) -> List[Track]:
        """
        Select optimal tracks with constraints.

        Args:
            scored_tracks: List of scored track dictionaries
            target_duration: Target duration in seconds

        Returns:
            List of selected Track objects
        """
        selected = []
        artist_count = {}
        current_duration = 0

        for item in scored_tracks:
            track = item["track"]

            # Check duration
            if current_duration + track.duration_ms / 1000 > target_duration * 1.15:
                continue

            # Check artist diversity (max 2 per artist)
            if artist_count.get(track.artist_id, 0) >= 2:
                continue

            # Check BPM transition (smooth < 15 BPM jump)
            if selected and abs(selected[-1].bpm - track.bpm) > 15:
                continue

            # Add track
            selected.append(track)
            current_duration += track.duration_ms / 1000
            artist_count[track.artist_id] = artist_count.get(
                track.artist_id, 0) + 1

            # Check if target reached
            if current_duration >= target_duration * 0.95:
                break

        return selected
