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
            max_iterations=5,  # More iterations for complex playlist creation
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
        # Try to extract JSON from output
        try:
            # Remove markdown code blocks if present
            cleaned = re.sub(r"```json\n?", "", output_text)
            cleaned = re.sub(r"```\n?", "", cleaned)
            cleaned = cleaned.strip()

            # Try parsing as JSON
            json_data = json.loads(cleaned)
            return PlaylistResponse(**json_data)
        except (json.JSONDecodeError, ValueError):
            pass

        # Try to find JSON object in text
        json_match = re.search(
            r'\{[^{}]*"playlist_name"[^{}]*\}', output_text, re.DOTALL)
        if json_match:
            try:
                json_data = json.loads(json_match.group())
                return PlaylistResponse(**json_data)
            except (json.JSONDecodeError, ValueError):
                pass

        # Use output parser
        try:
            return self.output_parser.parse(output_text)
        except Exception as e:
            logger.error(f"Failed to parse agent output: {e}")
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
            from app.services.spotify_service import SpotifyService
            from app.schemas.llm_responses import PlaylistTrack

            spotify_service = SpotifyService()
            sp = spotify_service.get_user_client("")  # Use client credentials

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
            target_tempo = (workout_intent.target_bpm_min + workout_intent.target_bpm_max) / 2
            recommendations = sp.recommendations(
                seed_genres=valid_genres[:5],
                target_tempo=target_tempo,
                min_tempo=workout_intent.target_bpm_min,
                max_tempo=workout_intent.target_bpm_max,
                limit=50,
            )

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
