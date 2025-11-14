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

        # Initialize MusicCuratorAgent if available and enabled
        if settings.USE_LANGCHAIN_CURATOR and MusicCuratorAgent:
            try:
                self.curator_agent = MusicCuratorAgent()
                self.use_langchain_curator = True
                logger.info("PlaylistGenerator: Using LangChain MusicCuratorAgent")
            except Exception as e:
                logger.warning(f"Failed to initialize MusicCuratorAgent: {e}")
                self.curator_agent = None
                self.use_langchain_curator = False
        else:
            self.curator_agent = None
            self.use_langchain_curator = False
            logger.info("PlaylistGenerator: Using legacy generation method")

    async def generate(
        self,
        workout: Workout,
        user_preferences: Dict,
        interval_stages: Optional[List[Dict]] = None,
        prompt: Optional[str] = None,
        user_token: Optional[str] = None,
        excluded_track_ids: Optional[List[str]] = None,
        workout_intent: Optional[Any] = None,  # WorkoutIntent from conversation (optional)
    ) -> PlaylistData:
        """
        Main generation method.

        Args:
            workout: Workout parameters
            user_preferences: User preferences (genres, artists, etc.)
            interval_stages: Custom interval stages (optional)
            prompt: Music prompt/description (optional)
            user_token: User's Spotify token (optional)
            excluded_track_ids: Track IDs to exclude (optional)
            workout_intent: WorkoutIntent from conversation (optional, for LangChain agent)

        Returns:
            PlaylistData with selected tracks
        """
        logger.info(
            f"Generating playlist for {workout.type} workout, {workout.duration_minutes} min"
        )

        # Try using MusicCuratorAgent if available
        if self.use_langchain_curator and self.curator_agent:
            try:
                logger.info("Using LangChain MusicCuratorAgent for playlist generation")
                from app.schemas.llm_responses import WorkoutIntent

                # Create WorkoutIntent from Workout if not provided
                if not workout_intent:
                    # Map workout.type to WorkoutIntent.workout_type
                    workout_type_map = {
                        "steady": "continuous",
                        "progressive": "continuous",  # Progressive is continuous with building energy
                        "intervals": "intervals",
                        "fartlek": "fartlek",
                    }
                    workout_type = workout_type_map.get(workout.type, "continuous")

                    # Get BPM from hr_zones
                    bpm_min = workout.hr_zones[0] if workout.hr_zones and len(workout.hr_zones) > 0 else 120
                    bpm_max = workout.hr_zones[1] if workout.hr_zones and len(workout.hr_zones) > 1 else 160

                    # Get genres and prompt from user_preferences
                    music_genres = user_preferences.get("top_genres", []) if isinstance(user_preferences, dict) else []
                    music_prompt = prompt

                    workout_intent = WorkoutIntent(
                        workout_type=workout_type,
                        duration_minutes=workout.duration_minutes,
                        target_bpm_min=bpm_min,
                        target_bpm_max=bpm_max,
                        intervals=None,  # Will be set from interval_stages if needed
                        energy_profile="steady",
                        music_genres=music_genres if music_genres else None,
                        music_prompt=music_prompt,
                        confidence=0.9,
                        needs_clarification=False,
                    )

                    # Add intervals if interval_stages provided
                    if interval_stages and workout_type in ["intervals", "fartlek"]:
                        from app.schemas.llm_responses import IntervalPhase
                        intervals = []
                        for stage in interval_stages:
                            phase_type = "work" if stage.get("hr_zone", 3) >= 3 else "rest"
                            bpm_range = stage.get("bpm_range", [bpm_min, bpm_max])
                            target_bpm = int((bpm_range[0] + bpm_range[1]) / 2)
                            intervals.append(IntervalPhase(
                                type=phase_type,
                                duration_minutes=stage.get("duration_minutes", 5),
                                target_bpm=target_bpm,
                            ))
                        workout_intent.intervals = intervals

                # Ensure workout_intent is WorkoutIntent instance
                if isinstance(workout_intent, dict):
                    workout_intent = WorkoutIntent(**workout_intent)
                elif not isinstance(workout_intent, WorkoutIntent):
                    logger.warning(f"Invalid workout_intent type: {type(workout_intent)}, falling back to legacy")
                    workout_intent = None

                if workout_intent:
                    # Use MusicCuratorAgent
                    playlist_response = await self.curator_agent.generate_playlist(
                        workout_intent=workout_intent,
                        user_id=user_preferences.get("user_id") if isinstance(user_preferences, dict) else None,
                        user_preferences=user_preferences,
                    )

                    # Convert PlaylistResponse to PlaylistData
                    tracks = []
                    for idx, track in enumerate(playlist_response.tracks):
                        # Convert PlaylistTrack to Track model
                        # Note: PlaylistTrack has different fields than Track
                        # We need to search for the track in Spotify to get full details
                        try:
                            # If track.id is available, try to use it directly
                            spotify_track = None
                            if track.id:
                                try:
                                    # Try to get track by ID (synchronous call, run in executor)
                                    import asyncio
                                    from functools import partial

                                    def get_track_sync(track_id, user_token):
                                        if user_token:
                                            user_client = self.spotify.get_user_client(user_token)
                                            return user_client.track(track_id)
                                        else:
                                            # Use client credentials
                                            from spotipy import Spotify
                                            from spotipy.oauth2 import SpotifyClientCredentials
                                            client_creds = SpotifyClientCredentials(
                                                client_id=self.spotify.client_credentials.client_id,
                                                client_secret=self.spotify.client_credentials.client_secret
                                            )
                                            sp = Spotify(auth_manager=client_creds)
                                            return sp.track(track_id)

                                    spotify_track = await asyncio.to_thread(get_track_sync, track.id, user_token)
                                except Exception as e:
                                    logger.debug(f"Failed to get track by ID {track.id}: {e}, searching by name")

                            # If no track found by ID, search by name
                            if not spotify_track:
                                spotify_track = await self.spotify.search_track_by_name(
                                    track_name=track.title,
                                    artist_name=track.artist,
                                    limit=1,
                                )

                            if spotify_track:
                                # Use Spotify track data
                                track_obj = Track(
                                    id=spotify_track.get("id", f"track_{idx}"),
                                    name=spotify_track.get("name", track.title),
                                    artist=spotify_track.get("artists", [{}])[0].get("name", track.artist),
                                    artist_id=spotify_track.get("artists", [{}])[0].get("id", ""),
                                    duration_ms=spotify_track.get("duration_ms", int(track.duration_seconds * 1000)),
                                    spotify_uri=spotify_track.get("uri", f"spotify:track:{spotify_track.get('id', '')}"),
                                    spotify_url=spotify_track.get("external_urls", {}).get("spotify", ""),
                                    preview_url=spotify_track.get("preview_url"),
                                    album=spotify_track.get("album", {}).get("name", "") if isinstance(spotify_track.get("album"), dict) else "",
                                    tempo=track.bpm,
                                    bpm=track.bpm,
                                    energy=track.energy_level,
                                    danceability=0.5,  # Default
                                    valence=0.5,  # Default
                                    genres=[track.genre] if track.genre else [],
                                )
                            else:
                                # Fallback: create track from PlaylistTrack data
                                track_id = f"llm_track_{idx}_{hash(track.title + track.artist) % 1000000}"
                                track_obj = Track(
                                    id=track_id,
                                    name=track.title,
                                    artist=track.artist,
                                    artist_id=track_id[:22],
                                    duration_ms=int(track.duration_seconds * 1000),
                                    spotify_uri=f"spotify:track:{track_id}",
                                    spotify_url="",
                                    preview_url=None,
                                    album="",
                                    tempo=track.bpm,
                                    bpm=track.bpm,
                                    energy=track.energy_level,
                                    danceability=0.5,
                                    valence=0.5,
                                    genres=[track.genre] if track.genre else [],
                                )
                            tracks.append(track_obj)
                        except Exception as e:
                            logger.warning(f"Failed to search track '{track.title}' by '{track.artist}': {e}")
                            # Create fallback track
                            track_id = f"llm_track_{idx}_{hash(track.title + track.artist) % 1000000}"
                            track_obj = Track(
                                id=track_id,
                                name=track.title,
                                artist=track.artist,
                                artist_id=track_id[:22],
                                duration_ms=int(track.duration_seconds * 1000),
                                spotify_uri=f"spotify:track:{track_id}",
                                spotify_url="",
                                preview_url=None,
                                album="",
                                tempo=track.bpm,
                                bpm=track.bpm,
                                energy=track.energy_level,
                                danceability=0.5,
                                valence=0.5,
                                genres=[track.genre] if track.genre else [],
                            )
                            tracks.append(track_obj)

                    # Filter excluded tracks if provided
                    if excluded_track_ids:
                        excluded_set = set(excluded_track_ids)
                        tracks = [t for t in tracks if t.id not in excluded_set]

                    total_duration = sum(t.duration_ms for t in tracks) / 1000

                    logger.info(
                        f"MusicCuratorAgent generated {len(tracks)} tracks, "
                        f"total duration: {total_duration:.1f}s"
                    )

                    return PlaylistData(
                        tracks=tracks,
                        total_duration=total_duration,
                        total_tracks=len(tracks),
                    )
            except Exception as e:
                logger.error(f"MusicCuratorAgent failed, falling back to legacy: {e}")
                # Fall through to legacy generation

        # Legacy generation method (fallback or default)
        logger.info("Using legacy playlist generation method")

        # 1. Create workout segments
        segments = self._create_segments(workout, interval_stages)
        logger.debug(f"Created {len(segments)} segments")

        # 2. Fetch candidate tracks (parallel)
        candidates = await self._fetch_candidates(
            segments, user_preferences, prompt, user_token
        )
        logger.debug(f"Fetched {len(candidates)} candidate tracks")

        # Filter out excluded tracks if provided
        if excluded_track_ids:
            excluded_set = set(excluded_track_ids)
            candidates = [c for c in candidates if c.id not in excluded_set]
            logger.debug(f"Filtered out {len(excluded_track_ids)} excluded tracks, {len(candidates)} remaining")

        # 3. Score tracks
        scored = self._score_tracks(candidates, segments, user_preferences)
        logger.debug(f"Scored {len(scored)} tracks")

        # 4. Optimize selection - ensure duration is longer than workout duration
        target_duration = workout.duration_minutes * 60
        selected = self._optimize_selection(scored, target_duration)
        logger.info(f"Selected {len(selected)} tracks for playlist")

        total_duration = sum(t.duration_ms for t in selected) / 1000

        return PlaylistData(
            tracks=selected,
            total_duration=total_duration,
            total_tracks=len(selected),
        )

    def _create_segments(
        self, workout: Workout, interval_stages: Optional[List[Dict]] = None
    ) -> List[Dict]:
        """
        Create workout segments with BPM ranges.

        Args:
            workout: Workout parameters
            interval_stages: Custom interval stages (for intervals type)

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
            # Intervals: use custom stages if provided, otherwise default
            if interval_stages and len(interval_stages) > 0:
                segments = []
                for stage in interval_stages:
                    segments.append(
                        {
                            "name": stage.get("name", "stage"),
                            "duration": stage.get("duration_minutes", 5),
                            "bpm_range": stage.get("bpm_range", [140, 160]),
                            "hr_zone": stage.get("hr_zone", [130, 150]),
                        }
                    )
                logger.info(
                    f"Using {len(segments)} custom interval stages"
                )
                return segments
            else:
                # Default: alternate between work and rest segments
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
        self,
        segments: List[Dict],
        user_prefs: Dict,
        prompt: Optional[str] = None,
        user_token: Optional[str] = None,
    ) -> List[Track]:
        """
        Fetch candidate tracks for all segments (parallel).

        Args:
            segments: List of workout segments
            user_prefs: User preferences

        Returns:
            List of Track objects
        """
        tasks = [
            self._fetch_for_segment(seg, user_prefs, prompt, user_token)
            for seg in segments
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_candidates = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error fetching tracks for segment {i} ({segments[i].get('name', 'unknown')}): {result}", exc_info=True)
                continue
            if isinstance(result, list):
                all_candidates.extend(result)
            else:
                logger.warning(f"Unexpected result type for segment {i}: {type(result)}")

        if not all_candidates:
            logger.warning("No tracks fetched for any segment - this may cause empty playlist")

        return all_candidates

    async def _fetch_for_segment(
        self,
        segment: Dict,
        user_prefs: Dict,
        prompt: Optional[str] = None,
        user_token: Optional[str] = None,
    ) -> List[Track]:
        """
        Fetch tracks for one segment.

        Args:
            segment: Segment dictionary with BPM range
            user_prefs: User preferences
            prompt: Optional user prompt for track search

        Returns:
            List of Track objects
        """
        try:
            bpm_min, bpm_max = segment["bpm_range"]
            target_bpm = int((bpm_min + bpm_max) / 2)

            logger.debug(
                f"Fetching tracks for segment {segment.get('name', 'unknown')}: "
                f"BPM {bpm_min}-{bpm_max}, target {target_bpm}"
            )

            # Use Spotify Recommendations API
            # Increase limit to ensure we have enough candidates for longer playlists
            # Try to use optimized method if available, otherwise fallback
            if hasattr(self.spotify, 'get_recommendations_optimized'):
                spotify_tracks = await self.spotify.get_recommendations_optimized(
                    seed_genres=user_prefs.get("top_genres", [])[:2],
                    seed_artists=user_prefs.get("top_artists", [])[:2],
                    target_tempo=target_bpm,
                    min_tempo=int(bpm_min),
                    max_tempo=int(bpm_max),
                    target_energy=0.7,  # High energy for workouts
                    limit=50,  # Increased from 20 to 50 for better selection
                    user_token=user_token,
                )
            else:
                spotify_tracks = await self.spotify.get_recommendations(
                    seed_genres=user_prefs.get("top_genres", [])[:2],
                    seed_artists=user_prefs.get("top_artists", [])[:2],
                    target_tempo=target_bpm,
                    min_tempo=int(bpm_min),
                    max_tempo=int(bpm_max),
                    target_energy=0.7,  # High energy for workouts
                    limit=50,  # Increased from 20 to 50 for better selection
                )

            if not spotify_tracks:
                logger.warning(f"No tracks returned from Spotify for segment {segment.get('name', 'unknown')}")
                spotify_tracks = []
        except Exception as e:
            logger.error(f"Error fetching Spotify recommendations: {e}", exc_info=True)
            spotify_tracks = []

        # If prompt is provided, try to enhance search with prompt-based query
        # This adds additional tracks that match the prompt description
        if prompt and prompt.strip():
            try:
                # Use search API with prompt to find additional relevant tracks
                # Try optimized method if available
                if hasattr(self.spotify, 'get_tracks_by_search_optimized'):
                    prompt_tracks = await self.spotify.get_tracks_by_search_optimized(
                        seed_genres=user_prefs.get("top_genres", [])[:2],
                        min_tempo=int(bpm_min),
                        max_tempo=int(bpm_max),
                        target_energy=0.7,
                        limit=10,
                        search_query=prompt,  # Add prompt to search
                    )
                else:
                    prompt_tracks = await self.spotify.get_tracks_by_search(
                        seed_genres=user_prefs.get("top_genres", [])[:2],
                        min_tempo=int(bpm_min),
                        max_tempo=int(bpm_max),
                        target_energy=0.7,
                        limit=10,
                        search_query=prompt,  # Add prompt to search
                    )
                # Merge prompt-based tracks with recommendations (avoid duplicates)
                existing_ids = {t.get("id") for t in spotify_tracks if t.get("id")}
                for track in prompt_tracks:
                    if track.get("id") and track.get("id") not in existing_ids:
                        spotify_tracks.append(track)
                        existing_ids.add(track.get("id"))
                logger.debug(f"Added {len(prompt_tracks)} prompt-based tracks")
            except Exception as e:
                logger.warning(f"Failed to search tracks with prompt: {e}")

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

        if not tracks:
            logger.warning(f"No valid tracks converted for segment {segment.get('name', 'unknown')}")

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
        Ensures duration is always longer than target_duration.
        Uses adaptive constraints - relaxes them if needed to reach minimum duration.

        Args:
            scored_tracks: List of scored track dictionaries
            target_duration: Target duration in seconds (minimum required)

        Returns:
            List of selected Track objects with duration >= target_duration
        """
        # Target duration - we want at least workout duration + 10% buffer
        # But minimum is workout duration
        target_duration_with_buffer = target_duration * 1.10
        min_required_duration = target_duration  # Absolute minimum

        # Try with strict constraints first (target: 10% longer than workout)
        selected = self._select_tracks_with_constraints(
            scored_tracks, target_duration_with_buffer,
            max_artist_tracks=2,
            max_bpm_jump=15,
            strict_mode=True
        )

        current_duration = sum(t.duration_ms for t in selected) / 1000

        # If we haven't reached minimum required duration, relax constraints
        if current_duration < min_required_duration:
            logger.warning(
                f"Playlist duration ({current_duration:.1f}s) is less than minimum required ({min_required_duration}s) with strict constraints. "
                f"Relaxing constraints to ensure minimum duration..."
            )

            # Relax BPM transition constraint (allow up to 25 BPM jump)
            # But target at least minimum required duration
            selected = self._select_tracks_with_constraints(
                scored_tracks, min_required_duration,
                max_artist_tracks=2,
                max_bpm_jump=25,
                strict_mode=False
            )
            current_duration = sum(t.duration_ms for t in selected) / 1000

            # If still not enough, relax artist constraint (allow up to 3 tracks per artist)
            if current_duration < min_required_duration:
                logger.warning(
                    f"Still insufficient duration ({current_duration:.1f}s). Relaxing artist constraint..."
                )
                selected = self._select_tracks_with_constraints(
                    scored_tracks, min_required_duration,
                    max_artist_tracks=3,
                    max_bpm_jump=25,
                    strict_mode=False
                )
                current_duration = sum(t.duration_ms for t in selected) / 1000

                # If still not enough, remove BPM transition constraint
                if current_duration < min_required_duration:
                    logger.warning(
                        f"Still insufficient duration ({current_duration:.1f}s). Removing BPM transition constraint..."
                    )
                    selected = self._select_tracks_with_constraints(
                        scored_tracks, min_required_duration,
                        max_artist_tracks=3,
                        max_bpm_jump=999,  # No BPM constraint
                        strict_mode=False
                    )
                    current_duration = sum(t.duration_ms for t in selected) / 1000

                    # Last resort: allow more tracks per artist and ignore name duplicates more
                    if current_duration < min_required_duration:
                        logger.warning(
                            f"Still insufficient duration ({current_duration:.1f}s). Using last resort: very relaxed constraints..."
                        )
                        selected = self._select_tracks_with_constraints(
                            scored_tracks, min_required_duration,
                            max_artist_tracks=5,  # Allow more tracks per artist
                            max_bpm_jump=999,  # No BPM constraint
                            strict_mode=False
                        )
                        current_duration = sum(t.duration_ms for t in selected) / 1000

        # Final check - if still insufficient, log error but return what we have
        if current_duration < target_duration:
            logger.error(
                f"CRITICAL: Playlist duration ({current_duration:.1f}s) is still less than target ({target_duration}s) "
                f"even with relaxed constraints. Returning {len(selected)} tracks."
            )
        else:
            logger.info(
                f"Playlist duration: {current_duration:.1f}s (target: {target_duration}s, "
                f"{((current_duration / target_duration - 1) * 100):.1f}% longer, {len(selected)} tracks)"
            )

        return selected

    def _select_tracks_with_constraints(
        self,
        scored_tracks: List[Dict],
        min_duration: float,  # seconds
        max_artist_tracks: int = 2,
        max_bpm_jump: int = 15,
        strict_mode: bool = True,
    ) -> List[Track]:
        """
        Select tracks with specified constraints.

        Args:
            scored_tracks: List of scored track dictionaries
            min_duration: Minimum duration in seconds
            max_artist_tracks: Maximum tracks per artist
            max_bpm_jump: Maximum BPM jump between consecutive tracks
            strict_mode: If True, enforce duplicate name check strictly

        Returns:
            List of selected Track objects
        """
        selected = []
        artist_count = {}
        track_names = set()  # Track unique track names
        current_duration = 0

        for item in scored_tracks:
            track = item["track"]
            track_duration_sec = track.duration_ms / 1000

            # Check artist diversity
            if artist_count.get(track.artist_id, 0) >= max_artist_tracks:
                continue

            # Check for duplicate track names (case-insensitive)
            # Only in strict mode to allow more flexibility if needed
            if strict_mode:
                track_name_lower = track.name.lower().strip()
                if track_name_lower in track_names:
                    continue
                track_names.add(track_name_lower)

            # Check BPM transition
            if max_bpm_jump < 999 and selected and abs(selected[-1].bpm - track.bpm) > max_bpm_jump:
                continue

            # Add track
            selected.append(track)
            if not strict_mode:
                # Still track names in non-strict mode, but allow same name from different artists
                track_name_lower = track.name.lower().strip()
                track_names.add(f"{track.artist_id}:{track_name_lower}")

            current_duration += track_duration_sec
            artist_count[track.artist_id] = artist_count.get(
                track.artist_id, 0) + 1

            # Continue until we exceed minimum duration
            if current_duration >= min_duration:
                break

        return selected
