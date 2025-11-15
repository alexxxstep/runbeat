"""
Playlist Generator - Core algorithm for generating workout playlists.
"""
from typing import List, Dict, Optional, Any
from app.models.workout import Workout
from app.models.playlist import Track, PlaylistData
from app.services.spotify_service import SpotifyService
from app.core.config import settings
from loguru import logger
import asyncio
import random
import math

# New import for the WorkoutProfiler
from app.services.workout_profiler import WorkoutProfiler, WorkoutSegment
from app.schemas.playlist import IntervalStage as IntervalStageSchema


# Conditional import for LangChain MusicCuratorAgent
MusicCuratorAgent = None
if settings.USE_LANGCHAIN_CURATOR:
    try:
        from app.agents.curator import MusicCuratorAgent
        logger.info("MusicCuratorAgent imported for PlaylistGenerator")
    except ImportError as e:
        logger.warning(f"MusicCuratorAgent not available: {e}")
        MusicCuratorAgent = None


class PlaylistGenerator:
    """
    Single-class playlist generator (simplified from 7 agents).
    Generates personalized workout playlists based on workout parameters.
    Supports both legacy generation and LangChain MusicCuratorAgent.
    """

    def __init__(self, spotify: SpotifyService):
        """
        Initialize playlist generator.

        Args:
            spotify: SpotifyService instance
        """
        self.spotify = spotify
        self.use_langchain_curator = False  # Disabled by default for new method

        # The new profiler will be used instead of the langchain agent for now
        # We can decide later how to integrate them if needed.
        logger.info("PlaylistGenerator: Initializing with new WorkoutProfiler method.")


    async def generate(
        self,
        workout: Workout,
        user_preferences: Dict,
        interval_stages: Optional[List[Dict]] = None,
        prompt: Optional[str] = None,
        user_token: Optional[str] = None,
        excluded_track_ids: Optional[List[str]] = None,
        variant_strategy: str = "primary", # New parameter for variants
    ) -> PlaylistData:
        """
        Main generation method using the new WorkoutProfiler.
        """
        logger.info(
            f"Generating playlist for {workout.type} workout ({workout.duration_minutes} min) "
            f"with strategy: {variant_strategy}"
        )

        # Convert interval_stages dict to Pydantic model for the profiler
        interval_stages_schema = None
        if interval_stages:
            interval_stages_schema = [IntervalStageSchema(**stage) for stage in interval_stages]

        # 1. Create a workout profile
        profiler = WorkoutProfiler(workout, user_preferences, interval_stages_schema)
        profile = profiler.create_profile(variant_strategy=variant_strategy)
        logger.debug(f"Created {len(profile)} segments for the workout profile.")

        # 2. Fetch tracks for each segment in the profile
        all_tracks = await self._fetch_tracks_for_profile(
            profile,
            user_token=user_token,
            excluded_track_ids=excluded_track_ids or []
        )

        # 3. Assemble the final playlist from the fetched tracks
        playlist = self._assemble_playlist_from_profile(
            all_tracks, profile, workout.duration_minutes * 60
        )

        total_duration = sum(t.duration_ms for t in playlist) / 1000
        logger.info(
            f"Generated a dynamic playlist with {len(playlist)} tracks. "
            f"Total duration: {total_duration:.1f}s"
        )

        return PlaylistData(
            tracks=playlist,
            total_duration=total_duration,
            total_tracks=len(playlist),
        )

    async def _fetch_tracks_for_profile(
        self,
        profile: List[WorkoutSegment],
        user_token: Optional[str],
        excluded_track_ids: List[str]
    ) -> Dict[str, List[Track]]:
        """Fetch all tracks for the entire profile, segment by segment."""

        tasks = []
        for segment in profile:
            tasks.append(self._fetch_tracks_for_segment(segment, user_token))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_tracks = {}
        # Keep track of all IDs used across the entire playlist generation
        used_track_ids = set(excluded_track_ids)

        for i, result in enumerate(results):
            segment_name = profile[i].name
            if isinstance(result, Exception):
                logger.error(f"Error fetching tracks for segment '{segment_name}': {result}")
                all_tracks[segment_name] = []
            elif isinstance(result, list):
                # Filter out tracks that have already been used
                unique_tracks = []
                for track in result:
                    if track.id not in used_track_ids:
                        unique_tracks.append(track)
                        used_track_ids.add(track.id)
                all_tracks[segment_name] = unique_tracks
                logger.debug(f"Fetched {len(unique_tracks)} unique tracks for segment '{segment_name}'")

        return all_tracks

    async def _fetch_tracks_for_segment(
        self,
        segment: WorkoutSegment,
        user_token: Optional[str]
    ) -> List[Track]:
        """Fetch candidate tracks for a single workout segment."""

        # Estimate number of tracks needed, with a buffer
        avg_track_duration_s = 210  # 3.5 minutes
        num_tracks_needed = math.ceil(segment.duration_seconds / avg_track_duration_s)
        limit = int(num_tracks_needed * 3) + 10 # Fetch plenty of candidates

        try:
            spotify_tracks = await self.spotify.get_recommendations(
            seed_genres=segment.genres[:2],
            seed_artists=[], # Add missing seed_artists
            target_tempo=int((segment.min_bpm + segment.max_bpm) / 2),
            min_tempo=segment.min_bpm,
            max_tempo=segment.max_bpm,
            target_energy=segment.target_energy,
            limit=limit,
            user_token=user_token,
            )

            if not spotify_tracks:
                logger.warning(f"No tracks returned from Spotify for segment '{segment.name}'")
                return []

            return [self._spotify_to_track(t) for t in spotify_tracks if t]

        except Exception as e:
            logger.error(f"Failed to fetch tracks for segment '{segment.name}': {e}")
            return []

    def _assemble_playlist_from_profile(
        self,
        all_tracks: Dict[str, List[Track]],
        profile: List[WorkoutSegment],
        target_duration_seconds: int
    ) -> List[Track]:
        """Fill each segment with tracks until the target duration is met."""
        playlist = []
        current_duration_ms = 0

        for segment in profile:
            segment_duration_ms = segment.duration_seconds * 1000
            filled_duration_ms = 0

            candidates = all_tracks.get(segment.name, [])
            # Sort candidates by energy to match the segment's mood
            candidates.sort(key=lambda t: t.energy, reverse=True)

            for track in candidates:
                if filled_duration_ms >= segment_duration_ms:
                    break
                playlist.append(track)
                filled_duration_ms += track.duration_ms
                current_duration_ms += track.duration_ms

        # If total duration is still too short, add more from the highest energy segment
        if current_duration_ms < target_duration_seconds * 1000:
             # Find the main segment with the most remaining candidates
            main_segments = [s for s in profile if s.type == 'main']
            if not main_segments:
                 main_segments = profile # fallback to any segment

            best_segment_name = max(main_segments, key=lambda s: len(all_tracks.get(s.name, [])), default=profile[0]).name

            extra_candidates = all_tracks.get(best_segment_name, [])
            for track in extra_candidates:
                if current_duration_ms >= target_duration_seconds * 1000:
                    break
                if track.id not in {t.id for t in playlist}:
                    playlist.append(track)
                    current_duration_ms += track.duration_ms

        return playlist


    def _spotify_to_track(self, spotify_track: Dict) -> Optional[Track]:
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

        if not track_id:
            return None

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
