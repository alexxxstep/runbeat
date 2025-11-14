"""
Modular prompt system for RunBeat LLM service.
"""
from app.services.prompts.prompt_builder import (
    ConversationState,
    PromptBuilder,
    PromptConfig,
    UserContext,
)
from app.services.prompts.workout_expert import WORKOUT_EXPERT_SYSTEM
from app.services.prompts.music_curator import (
    MUSIC_CURATOR_SYSTEM,
    MUSIC_CURATOR_EXAMPLES,
    GENRE_BPM_RANGES,
    WORKOUT_GENRES,
    INTENSITY_BPM,
    CurationStrategy,
    PlaylistValidationResult,
    validate_bpm_progression,
    validate_genre_coherence,
    validate_workout_phase_matching,
    validate_playlist,
    build_first_time_user_prompt,
    build_returning_user_prompt,
    build_genre_specific_prompt,
    build_mood_based_prompt,
    CurationStrategyConfig,
    get_curation_strategy_prompt,
)
from app.services.prompts.system_prompts import BASE_SYSTEM_PROMPT

__all__ = [
    "PromptBuilder",
    "PromptConfig",
    "UserContext",
    "ConversationState",
    "WORKOUT_EXPERT_SYSTEM",
    "MUSIC_CURATOR_SYSTEM",
    "MUSIC_CURATOR_EXAMPLES",
    "BASE_SYSTEM_PROMPT",
    # Music curator exports
    "GENRE_BPM_RANGES",
    "WORKOUT_GENRES",
    "INTENSITY_BPM",
    "CurationStrategy",
    "PlaylistValidationResult",
    "validate_bpm_progression",
    "validate_genre_coherence",
    "validate_workout_phase_matching",
    "validate_playlist",
    "build_first_time_user_prompt",
    "build_returning_user_prompt",
    "build_genre_specific_prompt",
    "build_mood_based_prompt",
    "CurationStrategyConfig",
    "get_curation_strategy_prompt",
]

