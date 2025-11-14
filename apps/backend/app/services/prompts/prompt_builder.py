"""
Prompt builder for combining system prompts and user context.
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from loguru import logger

from app.services.prompts.system_prompts import BASE_SYSTEM_PROMPT, PROMPT_VERSION
from app.services.prompts.workout_expert import WORKOUT_EXPERT_SYSTEM
from app.services.prompts.music_curator import (
    MUSIC_CURATOR_SYSTEM,
    MUSIC_CURATOR_EXAMPLES,
    build_first_time_user_prompt,
    build_returning_user_prompt,
    build_genre_specific_prompt,
    build_mood_based_prompt,
    get_curation_strategy_prompt,
    CurationStrategy,
)
from app.models.workout import Workout


class UserContext(BaseModel):
    """User context for personalizing prompts."""

    user_id: Optional[str] = Field(None, description="User ID")
    workout_history: Optional[List[Dict[str, Any]]] = Field(
        None, description="Previous workout history"
    )
    music_preferences: Optional[List[str]] = Field(
        None, description="Preferred music genres"
    )
    fitness_level: Optional[str] = Field(
        None, description="User fitness level (beginner/intermediate/advanced)"
    )
    language: Optional[str] = Field("en", description="Preferred language")


class ConversationState(BaseModel):
    """Conversation state for context-aware prompts."""

    messages: List[Dict[str, str]] = Field(
        default_factory=list, description="Previous messages in conversation"
    )
    current_intent: Optional[str] = Field(
        None, description="Current user intent")
    clarification_needed: bool = Field(
        default=False, description="Whether clarification is needed"
    )


class PromptConfig(BaseModel):
    """Configuration for prompt building."""

    include_workout_expert: bool = Field(
        default=True, description="Include workout expert knowledge"
    )
    include_music_curator: bool = Field(
        default=False, description="Include music curator knowledge"
    )
    response_format: str = Field(
        default="json", description="Response format (json/structured/conversational)"
    )
    prompt_version: str = Field(
        default=PROMPT_VERSION, description="Prompt version for A/B testing"
    )
    temperature: float = Field(
        default=0.3, description="LLM temperature for response"
    )
    max_tokens: int = Field(
        default=500, description="Maximum tokens in response")


class PromptBuilder:
    """Builder for constructing LLM prompts with modular components."""

    def __init__(self, config: Optional[PromptConfig] = None):
        """
        Initialize prompt builder.

        Args:
            config: Optional prompt configuration
        """
        self.config = config or PromptConfig()
        logger.debug(f"PromptBuilder initialized with config: {self.config}")

    def build_system_prompt(
        self,
        user_context: Optional[UserContext] = None,
    ) -> str:
        """
        Build system prompt from modular components.

        Args:
            user_context: Optional user context for personalization

        Returns:
            Combined system prompt string
        """
        components = []

        # Base system prompt
        if self.config.response_format == "json":
            components.append(BASE_SYSTEM_PROMPT)
        else:
            components.append(
                "You are RunBeat AI, an expert assistant for runners and workout music curation."
            )

        # Add workout expert knowledge
        if self.config.include_workout_expert:
            components.append("\n\n## Workout Expertise\n")
            components.append(WORKOUT_EXPERT_SYSTEM)

        # Add music curator knowledge
        if self.config.include_music_curator:
            components.append("\n\n## Music Curation Expertise\n")
            components.append(MUSIC_CURATOR_SYSTEM)

        # Add user context if provided
        if user_context:
            context_parts = []
            if user_context.fitness_level:
                context_parts.append(
                    f"User fitness level: {user_context.fitness_level}"
                )
            if user_context.music_preferences:
                context_parts.append(
                    f"Preferred genres: {', '.join(user_context.music_preferences)}"
                )
            if user_context.workout_history:
                context_parts.append(
                    f"Previous workouts: {len(user_context.workout_history)} recorded"
                )

            if context_parts:
                components.append("\n\n## User Context\n")
                components.append("\n".join(context_parts))

        return "\n".join(components)

    def build_workout_parsing_prompt(
        self,
        user_message: str,
        user_context: Optional[UserContext] = None,
        conversation_state: Optional[ConversationState] = None,
    ) -> str:
        """
        Build prompt for parsing workout intent from user message.

        Args:
            user_message: User's message/request
            user_context: Optional user context
            conversation_state: Optional conversation state

        Returns:
            Complete prompt for workout parsing
        """
        prompt_parts = []

        # Add context from conversation if available
        if conversation_state and conversation_state.messages:
            prompt_parts.append("## Conversation History\n")
            for msg in conversation_state.messages[-3:]:  # Last 3 messages
                role = msg.get("role", "user")
                content = msg.get("content", "")
                prompt_parts.append(f"{role.capitalize()}: {content}")

        # Main instruction
        prompt_parts.append("\n## Task\n")
        prompt_parts.append(
            "Parse the user's workout request into structured JSON format. "
            "IMPORTANT: If the user provides duration AND intensity/pace information, "
            "the intent is COMPLETE and you should set needs_clarification=false with high confidence (0.9+)."
        )
        prompt_parts.append(f'\nUser message: "{user_message}"\n')

        # Output format specification
        prompt_parts.append("## Output Format\n")
        prompt_parts.append(
            """Extract the following parameters:
{
  "type": "steady|progressive|intervals|fartlek",
  "duration_minutes": <number>,
  "intensity": "low|moderate|high",
  "hr_zones": [<min>, <max>],
  "confidence": <0-1>,
  "needs_clarification": <bool>,
  "clarification_question": "<string if needed>"
}"""
        )

        # Examples
        prompt_parts.append("\n## Examples\n")
        prompt_parts.append(
            '''"Хочу пробігти 40 хв з інтервалами" →
{
  "type": "intervals",
  "duration_minutes": 40,
  "intensity": "moderate",
  "hr_zones": [130, 180],
  "confidence": 0.8,
  "needs_clarification": true,
  "clarification_question": "Який буде інтервал роботи/відпочинку?"
}

"Легке відновлення 30 хвилин" →
{
  "type": "steady",
  "duration_minutes": 30,
  "intensity": "low",
  "hr_zones": [110, 130],
  "confidence": 0.95,
  "needs_clarification": false
}

"37 хв в легкому темпі" →
{
  "type": "steady",
  "duration_minutes": 37,
  "intensity": "low",
  "hr_zones": [110, 130],
  "confidence": 0.95,
  "needs_clarification": false
}

"Хочу пробігти 37 хв під легку мотивуючу музику" →
{
  "type": "steady",
  "duration_minutes": 37,
  "intensity": "low",
  "hr_zones": [110, 130],
  "confidence": 0.9,
  "needs_clarification": false
}

"Tempo run 45 minutes" →
{
  "type": "progressive",
  "duration_minutes": 45,
  "intensity": "moderate",
  "hr_zones": [140, 160],
  "confidence": 0.9,
  "needs_clarification": false
}'''
        )

        # Instructions
        prompt_parts.append(
            "\n## Instructions\n"
        )
        prompt_parts.append(
            """1. Use your workout expertise to interpret the user's intent
2. Map intensity keywords to appropriate HR zones and BPM:
   - "легкий", "легкому", "easy", "recovery", "відновлення" → low intensity → Zone 1-2 (110-130 BPM)
   - "темповий", "tempo", "помірний", "moderate" → moderate intensity → Zone 2-3 (130-160 BPM)
   - "швидкий", "fast", "інтервали", "intervals", "висока" → high intensity → Zone 4-5 (160-180 BPM)
3. When user provides duration AND intensity/pace, consider the intent COMPLETE
4. Infer missing parameters when possible (e.g., duration from workout type)
5. Set confidence HIGH (0.9+) when duration and intensity are clearly stated
6. Only ask clarifying questions when CRITICAL parameters are missing (e.g., intervals without work/rest ratio)
7. If conversation history contains previous clarification, use that context to complete the intent
8. Return ONLY valid JSON without markdown formatting"""
        )

        return "\n".join(prompt_parts)

    def build_playlist_generation_prompt(
        self,
        workout_intent: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]] = None,
        previous_playlists: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, str]]:
        """
        Build prompt for playlist generation with music curator expertise.

        Args:
            workout_intent: Parsed workout parameters (from WorkoutIntent)
            user_preferences: User's music preferences and history
            previous_playlists: User's previous playlists for learning

        Returns:
            List of messages for OpenAI API
        """
        system_prompt = self._build_music_curator_system_prompt(
            user_preferences=user_preferences,
            previous_playlists=previous_playlists,
        )

        user_prompt = self._build_playlist_request_prompt(
            workout_intent=workout_intent,
            user_preferences=user_preferences,
        )

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def _build_music_curator_system_prompt(
        self,
        user_preferences: Optional[Dict[str, Any]] = None,
        previous_playlists: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """
        Build music curator system prompt with user personalization.

        Args:
            user_preferences: User's music preferences
            previous_playlists: History for learning user taste

        Returns:
            Complete system prompt string
        """
        base_prompt = MUSIC_CURATOR_SYSTEM
        base_prompt += "\n\n" + MUSIC_CURATOR_EXAMPLES

        # Add user music preferences
        if user_preferences:
            base_prompt += "\n\n## User Music Profile\n"

            if "favorite_genres" in user_preferences or "top_genres" in user_preferences:
                genres = user_preferences.get(
                    "favorite_genres") or user_preferences.get("top_genres", [])
                if genres:
                    genres_str = ", ".join(genres) if isinstance(
                        genres, list) else genres
                    base_prompt += f"**Favorite Genres:** {genres_str}\n"

            if "disliked_genres" in user_preferences:
                disliked = ", ".join(user_preferences["disliked_genres"])
                base_prompt += f"**Avoid Genres:** {disliked}\n"

            if "energy_preference" in user_preferences:
                base_prompt += f"**Energy Preference:** {user_preferences['energy_preference']}\n"

            if "vocal_preference" in user_preferences:
                pref = user_preferences["vocal_preference"]
                base_prompt += f"**Vocal Preference:** {pref}\n"

        # Add learning from previous playlists
        if previous_playlists and len(previous_playlists) > 0:
            base_prompt += "\n## Learning from User History\n"

            # Analyze skip rates by genre
            genre_stats = self._analyze_previous_playlists(previous_playlists)

            if genre_stats:
                base_prompt += "Based on user's playlist history:\n"
                for genre, stats in genre_stats.items():
                    if stats["skip_rate"] < 0.2:
                        base_prompt += (
                            f"- ✓ {genre}: High engagement (skip rate {stats['skip_rate']:.0%})\n"
                        )
                    elif stats["skip_rate"] > 0.4:
                        base_prompt += (
                            f"- ✗ {genre}: Low engagement (skip rate {stats['skip_rate']:.0%}) - avoid\n"
                        )

        return base_prompt

    def _build_playlist_request_prompt(
        self,
        workout_intent: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Build user prompt for playlist generation request.

        Args:
            workout_intent: Parsed workout parameters
            user_preferences: User preferences for context

        Returns:
            User prompt string
        """
        prompt = f"""Generate a workout playlist with the following parameters:

**Workout Type:** {workout_intent.get('workout_type', workout_intent.get('type', 'steady'))}
**Duration:** {workout_intent.get('duration_minutes', 30)} minutes
**Target BPM Range:** {workout_intent.get('target_bpm_min', 120)}-{workout_intent.get('target_bpm_max', 160)}
**Energy Profile:** {workout_intent.get('energy_profile', 'steady')}
"""

        if workout_intent.get("intervals"):
            prompt += f"\n**Intervals:** {len(workout_intent['intervals'])} intervals\n"
            for i, interval in enumerate(workout_intent["intervals"], 1):
                prompt += (
                    f"  - Interval {i}: {interval.get('type', 'work')} for "
                    f"{interval.get('duration_minutes', 3)} min at "
                    f"{interval.get('target_bpm', 150)} BPM\n"
                )

        if workout_intent.get("mood"):
            prompt += f"\n**Mood:** {workout_intent['mood']}"

        if workout_intent.get("genre_preferences"):
            genres = ", ".join(workout_intent["genre_preferences"])
            prompt += f"\n**Genre Request:** {genres}"

        prompt += """

Please generate a complete playlist following the music curation principles.
Include:

1. Playlist overview (total tracks, duration, BPM progression)
2. Phase breakdown (warm-up, main, cool-down)
3. Complete track list with BPM, duration, energy level
4. Energy curve visualization
5. Curation notes explaining your choices
"""

        return prompt

    def _analyze_previous_playlists(
        self,
        previous_playlists: List[Dict[str, Any]],
    ) -> Dict[str, Dict[str, float]]:
        """
        Analyze user's previous playlists to learn preferences.

        Args:
            previous_playlists: List of past playlist data with engagement metrics

        Returns:
            Dictionary of genre statistics
        """
        genre_stats = {}

        for playlist in previous_playlists:
            for track in playlist.get("tracks", []):
                genre = track.get("genre", "unknown")
                if isinstance(genre, list):
                    genre = genre[0] if genre else "unknown"

                if genre not in genre_stats:
                    genre_stats[genre] = {
                        "total_tracks": 0,
                        "skipped_tracks": 0,
                        "skip_rate": 0.0,
                    }

                genre_stats[genre]["total_tracks"] += 1

                if track.get("skipped", False):
                    genre_stats[genre]["skipped_tracks"] += 1

        # Calculate skip rates
        for genre in genre_stats:
            total = genre_stats[genre]["total_tracks"]
            skipped = genre_stats[genre]["skipped_tracks"]
            genre_stats[genre]["skip_rate"] = skipped / \
                total if total > 0 else 0.0

        return genre_stats

    def build_music_curation_prompt(
        self,
        workout: Workout,
        user_context: Optional[UserContext] = None,
        scenario: Optional[str] = None,
        requested_genres: Optional[List[str]] = None,
        mood: Optional[str] = None,
        curation_strategy: Optional[CurationStrategy] = None,
    ) -> str:
        """
        Build prompt for music curation based on scenario.

        Args:
            workout: Workout parameters
            user_context: Optional user context
            scenario: Scenario type (first_time, returning, genre_specific, mood_based)
            requested_genres: List of requested genres (for genre_specific scenario)
            mood: Desired mood (for mood_based scenario)
            curation_strategy: Optional A/B testing strategy

        Returns:
            Complete prompt for music curation
        """
        prompt_parts = []

        # Add strategy-specific prompt if provided
        if curation_strategy:
            prompt_parts.append(
                get_curation_strategy_prompt(curation_strategy, workout)
            )
            prompt_parts.append("")

        # Build scenario-specific prompt
        user_prefs = None
        if user_context:
            user_prefs = {
                "top_genres": user_context.music_preferences or [],
                "top_artists": [],
            }

        if scenario == "first_time" or (
            scenario is None and (
                not user_context or not user_context.workout_history)
        ):
            prompt_parts.append(
                build_first_time_user_prompt(workout, user_prefs)
            )
        elif scenario == "returning" or (
            scenario is None
            and user_context
            and user_context.workout_history
            and len(user_context.workout_history) > 0
        ):
            prompt_parts.append(
                build_returning_user_prompt(
                    workout,
                    user_context.workout_history or [],
                    user_prefs,
                )
            )
        elif scenario == "genre_specific" and requested_genres:
            prompt_parts.append(
                build_genre_specific_prompt(
                    workout, requested_genres, user_prefs)
            )
        elif scenario == "mood_based" and mood:
            prompt_parts.append(
                build_mood_based_prompt(workout, mood, user_prefs)
            )
        else:
            # Default: first-time user prompt
            prompt_parts.append(
                build_first_time_user_prompt(workout, user_prefs))

        return "\n".join(prompt_parts)

    def build_messages(
        self,
        user_message: str,
        user_context: Optional[UserContext] = None,
        conversation_state: Optional[ConversationState] = None,
        task: str = "parse_workout",
    ) -> List[Dict[str, str]]:
        """
        Build complete message list for OpenAI API.

        Args:
            user_message: User's message
            user_context: Optional user context
            conversation_state: Optional conversation state
            task: Task type (parse_workout, curate_music, etc.)

        Returns:
            List of messages for OpenAI API
        """
        messages = []

        # Build system prompt
        system_prompt = self.build_system_prompt(user_context=user_context)
        messages.append({"role": "system", "content": system_prompt})

        # Build user prompt based on task
        if task == "parse_workout":
            user_prompt = self.build_workout_parsing_prompt(
                user_message=user_message,
                user_context=user_context,
                conversation_state=conversation_state,
            )
        elif task == "curate_music":
            # For music curation, we need workout from user_message or context
            # This is a simplified version - in practice, workout would come from context
            # For now, use user message directly with music curator system prompt
            user_prompt = user_message
        else:
            # Default: use user message directly
            user_prompt = user_message

        messages.append({"role": "user", "content": user_prompt})

        return messages

    def get_model_params(self) -> Dict[str, Any]:
        """
        Get model parameters for OpenAI API call.

        Returns:
            Dictionary with model parameters
        """
        return {
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }
