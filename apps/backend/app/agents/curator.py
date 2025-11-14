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
            logger.error(f"Error generating playlist: {e}")
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
