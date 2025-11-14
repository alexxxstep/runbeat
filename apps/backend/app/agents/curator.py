"""
Music Curator Agent using LangChain.
"""
from typing import Optional, Dict, Any
import json
import re
from loguru import logger

from langchain.agents import AgentExecutor, create_structured_chat_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.agents.base import BaseAgent
from app.agents.tools.spotify_tools import (
    search_spotify_tracks,
    get_spotify_recommendations,
    calculate_bpm_progression,
)
from app.agents.tools.database_tools import (
    get_user_preferences,
    get_user_music_history,
)
from app.agents.prompts.curator_prompts import (
    CURATOR_AGENT_SYSTEM_PROMPT,
    CURATOR_AGENT_USER_PROMPT_TEMPLATE,
    OUTPUT_PARSER,
)
from app.schemas.llm_responses import PlaylistResponse, WorkoutIntent


class MusicCuratorAgent(BaseAgent):
    """
    LangChain-based music curator agent.

    Creates personalized workout playlists based on workout parameters,
    user preferences, and music science.
    """

    def __init__(self):
        """Initialize MusicCuratorAgent."""
        super().__init__(temperature=0.7, max_tokens=2000)  # Higher temp for creativity
        self.output_parser = OUTPUT_PARSER

        # Tools
        self.tools = [
            search_spotify_tracks,
            get_spotify_recommendations,
            calculate_bpm_progression,
            get_user_preferences,
            get_user_music_history,
        ]

        # Prompt (must include {tools}, {tool_names}, and {agent_scratchpad})
        # Format the prompt with format_instructions (use replace to avoid formatting {tools} and {tool_names})
        # Escape JSON schema braces in format_instructions to avoid LangChain variable parsing
        format_instructions = OUTPUT_PARSER.get_format_instructions()
        # Escape all braces in format_instructions (they're part of JSON schema, not LangChain variables)
        format_instructions_escaped = format_instructions.replace(
            "{", "{{").replace("}", "}}")

        system_prompt = CURATOR_AGENT_SYSTEM_PROMPT.replace(
            "{format_instructions}",
            format_instructions_escaped
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}\n\n{agent_scratchpad}"),
        ])

        # Agent
        self.agent = create_structured_chat_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt,
        )

        # Agent executor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            memory=self.memory,
            verbose=False,
            handle_parsing_errors=True,
            max_iterations=8,  # Reduced to avoid timeout, but still enough for playlist creation
            max_execution_time=45,  # 45 seconds max execution time per playlist (reduced to avoid timeout)
        )

        logger.info("MusicCuratorAgent initialized with LangChain")

    async def process(self, input_data: Dict[str, Any]) -> PlaylistResponse:
        """
        Process playlist generation request.

        Args:
            input_data: Dict with 'workout_intent' and optional 'user_id', 'user_preferences'

        Returns:
            PlaylistResponse with curated playlist
        """
        workout_intent = input_data.get("workout_intent")
        user_id = input_data.get("user_id")
        user_preferences = input_data.get("user_preferences")

        return await self.generate_playlist(
            workout_intent=workout_intent,
            user_id=user_id,
            user_preferences=user_preferences,
        )

    async def generate_playlist(
        self,
        workout_intent: WorkoutIntent,
        user_id: Optional[str] = None,
        user_preferences: Optional[Dict[str, Any]] = None,
    ) -> PlaylistResponse:
        """
        Generate workout playlist.

        Args:
            workout_intent: Workout intent with parameters
            user_id: Optional user ID for preferences
            user_preferences: Optional user preferences dict

        Returns:
            PlaylistResponse with curated playlist
        """
        logger.info(
            f"Generating playlist for {workout_intent.workout_type} workout, "
            f"{workout_intent.duration_minutes} min, "
            f"BPM {workout_intent.target_bpm_min}-{workout_intent.target_bpm_max}"
        )

        # Build user prompt
        genres = ", ".join(
            workout_intent.music_genres) if workout_intent.music_genres else "any"
        music_prompt = workout_intent.music_prompt or "none"

        user_prompt = CURATOR_AGENT_USER_PROMPT_TEMPLATE.format(
            workout_type=workout_intent.workout_type,
            duration_minutes=workout_intent.duration_minutes,
            bpm_min=workout_intent.target_bpm_min,
            bpm_max=workout_intent.target_bpm_max,
            genres=genres,
            music_prompt=music_prompt,
        )

        # Add user preferences context if available
        if user_id:
            user_prompt += f"\n\nUser ID: {user_id}\nUse get_user_preferences tool to get user's music preferences."

        try:
            # Invoke agent
            result = await self.agent_executor.ainvoke({
                "input": user_prompt,
            })

            # Extract output
            output_text = result.get("output", "")

            # Parse output
            playlist = self._parse_agent_output(output_text)

            logger.info(
                f"Generated playlist: {playlist.total_tracks} tracks, "
                f"{playlist.total_duration_minutes:.1f} min"
            )

            return playlist

        except Exception as e:
            error_str = str(e)
            logger.error(f"Error generating playlist: {e}")

            # Check if it's a rate limit error
            if "rate_limit" in error_str.lower() or "429" in error_str or "rate limit" in error_str.lower():
                logger.warning("OpenAI rate limit reached, using fallback playlist generation")
                # Wait a bit and try fallback with direct Spotify API
                import asyncio
                await asyncio.sleep(2)  # Brief wait
                return await self._create_fallback_playlist_with_spotify(workout_intent)

            # Check if agent stopped due to iteration/time limit
            if "iteration limit" in error_str.lower() or "time limit" in error_str.lower() or "execution time" in error_str.lower():
                logger.warning("Agent reached iteration/time limit, using Spotify fallback")
                return await self._create_fallback_playlist_with_spotify(workout_intent)

            # Fallback: create minimal playlist
            return self._create_fallback_playlist(workout_intent)

    def _parse_agent_output(self, output_text: str) -> PlaylistResponse:
        """
        Parse agent output into PlaylistResponse.

        Args:
            output_text: Agent output text

        Returns:
            PlaylistResponse instance
        """
        # Check if output indicates iteration/time limit was reached
        if not output_text or not output_text.strip():
            raise ValueError("Agent returned empty output")

        output_lower = output_text.lower()
        if "iteration limit" in output_lower or "time limit" in output_lower or "execution time" in output_lower:
            raise ValueError(f"Agent stopped due to iteration/time limit: {output_text}")

        # Try to extract JSON from output
        try:
            # Remove markdown code blocks if present
            cleaned = re.sub(r"```json\n?", "", output_text)
            cleaned = re.sub(r"```\n?", "", cleaned)
            cleaned = cleaned.strip()

            # Skip if empty after cleaning
            if not cleaned:
                raise ValueError("Output is empty after cleaning")

            # Try parsing as JSON
            json_data = json.loads(cleaned)
            return PlaylistResponse(**json_data)
        except (json.JSONDecodeError, ValueError) as e:
            logger.debug(f"Failed to parse as direct JSON: {e}")
            pass

        # Try to find JSON object in text
        json_match = re.search(
            r'\{[^{}]*"playlist_name"[^{}]*\}', output_text, re.DOTALL)
        if json_match:
            try:
                json_data = json.loads(json_match.group())
                return PlaylistResponse(**json_data)
            except (json.JSONDecodeError, ValueError) as e:
                logger.debug(f"Failed to parse JSON from match: {e}")
                pass

        # Use output parser
        try:
            return self.output_parser.parse(output_text)
        except Exception as e:
            logger.error(f"Failed to parse agent output: {e}")
            # If parsing fails and output contains iteration/time limit message, raise specific error
            if "iteration limit" in output_text.lower() or "time limit" in output_text.lower():
                raise ValueError(f"Agent stopped due to iteration/time limit: {output_text}")
            raise ValueError(f"Failed to parse playlist: {output_text}")

    def _create_fallback_playlist(self, workout_intent: WorkoutIntent) -> PlaylistResponse:
        """
        Create fallback playlist if agent fails.

        Args:
            workout_intent: Workout intent

        Returns:
            Minimal PlaylistResponse
        """
        logger.warning("Creating fallback playlist")

        from app.schemas.llm_responses import PlaylistTrack

        # Create minimal tracks
        tracks = []
        avg_bpm = (workout_intent.target_bpm_min +
                   workout_intent.target_bpm_max) / 2
        tracks_per_minute = 0.25  # ~4 min per track
        num_tracks = max(
            5, int(workout_intent.duration_minutes * tracks_per_minute))

        for i in range(num_tracks):
            tracks.append(PlaylistTrack(
                title=f"Track {i+1}",
                artist="Various Artists",
                duration_seconds=240,  # 4 minutes
                bpm=float(avg_bpm),
                energy_level=0.7,
                genre="pop",
                phase="main",
            ))

        return PlaylistResponse(
            playlist_name=f"{workout_intent.workout_type.capitalize()} Workout Playlist",
            tracks=tracks,
            bpm_range=[workout_intent.target_bpm_min,
                       workout_intent.target_bpm_max],
            total_tracks=len(tracks),
            total_duration_minutes=sum(
                t.duration_seconds for t in tracks) / 60,
            progression_type="steady",
            primary_genres=["pop"],
            curation_notes="Fallback playlist - please try again for better results.",
        )

    async def _create_fallback_playlist_with_spotify(
        self, workout_intent: WorkoutIntent
    ) -> PlaylistResponse:
        """
        Create fallback playlist using Spotify API directly (bypassing agent).

        Args:
            workout_intent: Workout intent

        Returns:
            PlaylistResponse with tracks from Spotify
        """
        logger.info("Creating fallback playlist using Spotify API directly")

        try:
            import spotipy
            from spotipy.oauth2 import SpotifyClientCredentials
            from app.core.config import settings
            from app.schemas.llm_responses import PlaylistTrack

            # Use client credentials instead of user token
            client_credentials = SpotifyClientCredentials(
                client_id=settings.SPOTIFY_CLIENT_ID,
                client_secret=settings.SPOTIFY_CLIENT_SECRET,
            )
            sp = spotipy.Spotify(client_credentials_manager=client_credentials)

            # Get genres from workout intent
            genres = workout_intent.music_genres or ["pop", "electronic"]
            # Map to valid Spotify genres
            valid_genres = []
            for genre in genres[:5]:
                genre_lower = genre.lower().strip()
                # Simple mapping
                if genre_lower in ["pop", "rock", "electronic", "edm", "house", "techno",
                                   "trance", "hip-hop", "r&b", "country", "jazz", "classical",
                                   "ambient", "chill", "folk", "metal", "punk", "indie"]:
                    valid_genres.append(genre_lower)

            if not valid_genres:
                valid_genres = ["pop", "electronic"]

            # Get recommendations
            # Spotify API doesn't accept target_tempo together with min_tempo/max_tempo
            # Use min_tempo and max_tempo to define the range
            target_tempo = (workout_intent.target_bpm_min + workout_intent.target_bpm_max) / 2

            # Ensure BPM range is valid (Spotify accepts 60-200 BPM)
            bpm_min = max(60, min(200, int(workout_intent.target_bpm_min)))
            bpm_max = max(60, min(200, int(workout_intent.target_bpm_max)))
            if bpm_min > bpm_max:
                bpm_min, bpm_max = bpm_max, bpm_min

            # Ensure we have at least one valid genre
            seed_genres_list = valid_genres[:5] if valid_genres else ["pop", "electronic"]

            # OPTIMIZATION: Get seed tracks first (more reliable than seed_genres)
            # Spotify Recommendations API works better with seed_tracks
            seed_tracks_list = []
            try:
                # Search for tracks by genre to use as seeds
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
                            "edm": "edm music",
                            "trance": "trance music",
                        }
                        search_term = genre_map.get(genre.lower(), genre)
                        search_results = sp.search(
                            q=search_term,
                            type="track",
                            limit=3,
                            market="US"
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
                        logger.debug(f"Genre search for {genre} failed: {genre_search_error}")
                        continue
            except Exception as seed_error:
                logger.debug(f"Failed to get seed tracks: {seed_error}")

            # Build recommendations parameters
            # IMPORTANT: Spotify API doesn't accept target_energy with min/max_tempo together
            # Try different combinations in order of preference

            # Add seeds first (required)
            base_params = {
                "limit": 50,
            }

            if seed_tracks_list:
                base_params["seed_tracks"] = seed_tracks_list[:5]
                logger.debug(f"Using {len(seed_tracks_list)} track seeds for recommendations")
            elif seed_genres_list:
                base_params["seed_genres"] = seed_genres_list[:5]
                logger.debug(f"Using {len(seed_genres_list)} genre seeds for recommendations")
            else:
                # Fallback: use default genres
                base_params["seed_genres"] = ["pop", "electronic"]
                logger.warning("No seeds available, using default genres")

            # Try recommendations with different parameter combinations
            recommendations = None
            last_error = None

            # Strategy 1: Try with tempo only (no target_energy)
            try:
                rec_params = base_params.copy()
                rec_params["min_tempo"] = bpm_min
                rec_params["max_tempo"] = bpm_max
                logger.debug(f"Attempting Spotify recommendations with tempo only: {list(rec_params.keys())}")
                recommendations = sp.recommendations(**rec_params)
                logger.debug("Spotify recommendations successful with tempo only")
            except Exception as e1:
                last_error = e1
                error_str = str(e1).lower()
                logger.debug(f"Recommendations with tempo failed: {e1}")

                # Strategy 2: Try with target_energy only (no tempo)
                if "404" in error_str or "not found" in error_str or "parameter" in error_str:
                    try:
                        rec_params = base_params.copy()
                        rec_params["target_energy"] = 0.7
                        logger.debug(f"Attempting Spotify recommendations with energy only: {list(rec_params.keys())}")
                        recommendations = sp.recommendations(**rec_params)
                        logger.debug("Spotify recommendations successful with energy only")
                    except Exception as e2:
                        last_error = e2
                        error_str2 = str(e2).lower()
                        logger.debug(f"Recommendations with energy failed: {e2}")

                        # Strategy 3: Try with target_tempo (single value, not range)
                        if "404" in error_str2 or "not found" in error_str2:
                            try:
                                rec_params = base_params.copy()
                                rec_params["target_tempo"] = int(target_tempo)
                                logger.debug(f"Attempting Spotify recommendations with target_tempo: {list(rec_params.keys())}")
                                recommendations = sp.recommendations(**rec_params)
                                logger.debug("Spotify recommendations successful with target_tempo")
                            except Exception as e3:
                                last_error = e3
                                error_str3 = str(e3).lower()
                                logger.debug(f"Recommendations with target_tempo failed: {e3}")

                                # Strategy 4: Minimal request (only seeds)
                                if "404" in error_str3 or "not found" in error_str3:
                                    try:
                                        logger.debug(f"Attempting Spotify recommendations with minimal params: {list(base_params.keys())}")
                                        recommendations = sp.recommendations(**base_params)
                                        logger.debug("Spotify recommendations successful with minimal params")
                                    except Exception as e4:
                                        last_error = e4
                                        logger.error(f"All recommendation strategies failed. Last error: {e4}")
                                        raise Exception(f"Failed to get recommendations from Spotify. Last error: {e4}")
                                else:
                                    raise e3
                        else:
                            raise e2
                else:
                    raise e1

            if recommendations is None:
                if last_error:
                    raise last_error
                raise Exception("Failed to get recommendations from Spotify")

            tracks = []
            total_duration = 0
            target_duration = workout_intent.duration_minutes * 60  # seconds

            for track in recommendations.get("tracks", []):
                duration_seconds = track.get("duration_ms", 0) / 1000
                if total_duration + duration_seconds > target_duration * 1.2:  # 20% buffer
                    break

                # Try to get audio features (may fail with 403)
                bpm = target_tempo
                try:
                    features = sp.audio_features([track.get("id")])[0]
                    if features and features.get("tempo"):
                        bpm = features.get("tempo")
                except Exception:
                    pass  # Use default BPM

                tracks.append(PlaylistTrack(
                    title=track.get("name", "Unknown"),
                    artist=", ".join([a["name"] for a in track.get("artists", [])]),
                    duration_seconds=duration_seconds,
                    bpm=float(bpm),
                    energy_level=0.7,
                    genre=valid_genres[0] if valid_genres else "pop",
                    phase="main",
                ))
                total_duration += duration_seconds

            if not tracks:
                # If no tracks, return minimal fallback
                return self._create_fallback_playlist(workout_intent)

            return PlaylistResponse(
                playlist_name=f"{workout_intent.workout_type.capitalize()} Workout Playlist",
                tracks=tracks,
                bpm_range=[workout_intent.target_bpm_min, workout_intent.target_bpm_max],
                total_tracks=len(tracks),
                total_duration_minutes=total_duration / 60,
                progression_type="steady",
                primary_genres=valid_genres[:3] if valid_genres else ["pop"],
                curation_notes="Fallback playlist (generated via Spotify API)",
            )
        except Exception as e:
            logger.error(f"Error in Spotify fallback: {e}")
            # Final fallback
            return self._create_fallback_playlist(workout_intent)
