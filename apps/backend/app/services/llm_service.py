"""
LLM Service for OpenAI GPT-4 integration.
"""
from typing import Any, Dict, List, Optional

from loguru import logger
from openai import AsyncOpenAI
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.llm_responses import PlaylistResponse, WorkoutIntent
from app.services.prompts.prompt_builder import (
    ConversationState,
    PromptBuilder,
    PromptConfig,
    UserContext,
)
from app.services.prompts.workout_expert import WORKOUT_EXPERT_SYSTEM


class LLMService:
    """Service for interacting with OpenAI GPT-4."""

    def __init__(self, prompt_config: Optional[PromptConfig] = None):
        """
        Initialize OpenAI client and prompt builder.

        Args:
            prompt_config: Optional prompt configuration for PromptBuilder
        """
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.prompt_builder = PromptBuilder(config=prompt_config)
        logger.info(
            f"LLMService initialized with model: {settings.OPENAI_MODEL}"
        )

    async def parse_workout(
        self,
        user_message: str,
        user_context: Optional[UserContext] = None,
        conversation_state: Optional[ConversationState] = None,
        prompt: Optional[str] = None,
    ) -> WorkoutIntent:
        """
        Parse workout intent using GPT-4 with OpenAI structured outputs.

        Args:
            user_message: User's message/request
            user_context: Optional user context for personalization
            conversation_state: Optional conversation state for context
            prompt: Optional legacy prompt string (for backward compatibility)

        Returns:
            WorkoutIntent with parsed workout parameters

        Raises:
            ValueError: If OpenAI API call fails or validation fails
            ValidationError: If structured output validation fails
        """
        try:
            # Use legacy prompt if provided, otherwise use new prompt builder
            if prompt:
                messages = [
                    {
                        "role": "system",
                        "content": WORKOUT_EXPERT_SYSTEM,
                    },
                    {"role": "user", "content": prompt},
                ]
                model_params = {"temperature": 0.3, "max_tokens": 500}
            else:
                messages = self.prompt_builder.build_messages(
                    user_message=user_message,
                    user_context=user_context,
                    conversation_state=conversation_state,
                    task="parse_workout",
                )
                model_params = self.prompt_builder.get_model_params()

            # Use OpenAI structured outputs with Pydantic model
            response = await self.client.beta.chat.completions.parse(
                model=settings.OPENAI_MODEL,
                messages=messages,
                response_format=WorkoutIntent,
                **model_params,
            )

            # Extract parsed response
            parsed = response.choices[0].message.parsed

            if not parsed:
                raise ValueError("Empty parsed response from OpenAI")

            # Validate the parsed response
            # (should already be validated by OpenAI)
            if not isinstance(parsed, WorkoutIntent):
                raise ValueError(
                    f"Unexpected response type: {type(parsed)}. "
                    f"Expected WorkoutIntent."
                )

            logger.debug(f"Parsed workout intent: {parsed.model_dump()}")
            return parsed

        except ValidationError as e:
            logger.error(f"Validation error for structured output: {e}")
            response_content = (
                response.choices[0].message.content
                if "response" in locals()
                else "N/A"
            )
            logger.error(f"Response: {response_content}")
            raise ValueError(f"Invalid structured output from OpenAI: {e}")
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            if isinstance(e, ValueError):
                raise
            raise ValueError(f"Failed to parse workout intent: {str(e)}")

    async def generate_playlist(
        self,
        workout_intent: WorkoutIntent,
        user_preferences: Optional[Dict[str, Any]] = None,
        previous_playlists: Optional[List[Dict[str, Any]]] = None,
    ) -> PlaylistResponse:
        """
        Generate playlist using music curator expertise.

        Args:
            workout_intent: Parsed workout parameters
            user_preferences: User's music preferences
            previous_playlists: Previous playlists for personalization

        Returns:
            PlaylistResponse with complete playlist

        Raises:
            Exception: If playlist generation fails
        """
        try:
            # Build music curator prompt
            messages = self.prompt_builder.build_playlist_generation_prompt(
                workout_intent=workout_intent.model_dump(),
                user_preferences=user_preferences,
                previous_playlists=previous_playlists,
            )

            logger.info(
                f"Generating playlist: type={workout_intent.workout_type}, "
                f"duration={workout_intent.duration_minutes}min, "
                f"BPM={workout_intent.target_bpm_min}-"
                f"{workout_intent.target_bpm_max}"
            )

            # Use structured outputs for playlist response
            response = await self.client.beta.chat.completions.parse(
                model=settings.OPENAI_MODEL,
                messages=messages,
                response_format=PlaylistResponse,
                temperature=0.7,  # Higher for creative curation
                max_tokens=3000,
            )

            playlist = response.choices[0].message.parsed

            if not playlist:
                raise ValueError("Empty playlist response from OpenAI")

            logger.info(
                f"✓ Generated playlist: {len(playlist.tracks)} tracks, "
                f"{playlist.total_duration_minutes} minutes"
            )

            return playlist

        except ValidationError as e:
            logger.error(f"Validation error for playlist response: {e}")
            response_content = (
                response.choices[0].message.content
                if "response" in locals()
                else "N/A"
            )
            logger.error(f"Response: {response_content}")
            raise ValueError(f"Invalid playlist response from OpenAI: {e}")
        except Exception as e:
            logger.error(f"Failed to generate playlist: {e}")
            if isinstance(e, ValueError):
                raise
            raise ValueError(f"Failed to generate playlist: {str(e)}")
