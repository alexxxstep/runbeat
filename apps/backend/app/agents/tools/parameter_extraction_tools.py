"""
LangChain tools for extracting workout parameters from conversation.
AI-driven parameter extraction through structured prompts.
"""
import json
from typing import Dict, Any
from langchain.tools import tool
from loguru import logger


@tool
def extract_workout_parameters(
    user_message: str,
    conversation_history: str,
    current_params: str
) -> str:
    """
    Extract workout parameters from conversation context using AI analysis.

    This tool analyzes the user's message in the context of conversation history
    and currently collected parameters to extract structured workout information.

    The AI should analyze:
    1. What did the user just say?
    2. What parameters were mentioned in previous messages?
    3. What new information can be extracted?
    4. What parameters are still missing?

    Args:
        user_message: Current user message to analyze
        conversation_history: JSON string of previous messages [{"role": "user/assistant", "content": "..."}]
        current_params: JSON string of currently collected parameters

    Returns:
        JSON string with extracted parameters:
        {
            "duration_minutes": int or null,
            "intensity": "low" | "moderate" | "high" | null,
            "workout_type": "steady" | "intervals" | "fartlek" | null,
            "genres": ["genre1", "genre2"] or [],
            "all_collected": boolean (true if duration, intensity, and genres present)
        }

    Examples:
        User: "інтервальна 45 хвилин"
        Returns: {"duration_minutes": 45, "workout_type": "intervals", "intensity": null, "genres": [], "all_collected": false}

        User: "електро"
        Current: {"duration_minutes": 45, "workout_type": "intervals"}
        Returns: {"duration_minutes": 45, "workout_type": "intervals", "intensity": null, "genres": ["electronic"], "all_collected": false}
    """
    try:
        # Parse inputs
        try:
            history = json.loads(conversation_history) if conversation_history else []
        except json.JSONDecodeError:
            history = []
            logger.warning(f"Failed to parse conversation_history: {conversation_history[:100]}")

        try:
            params = json.loads(current_params) if current_params else {}
        except json.JSONDecodeError:
            params = {}
            logger.warning(f"Failed to parse current_params: {current_params[:100]}")

        # Extract parameters from current message
        extracted = _extract_from_message(user_message)

        # Merge with current parameters (accumulate, don't overwrite)
        merged = _merge_parameters(params, extracted)

        # Check if all required parameters are collected
        merged["all_collected"] = _check_all_collected(merged)

        logger.debug(
            f"Parameter extraction: user_message='{user_message[:50]}...', "
            f"extracted={extracted}, merged={merged}"
        )

        return json.dumps(merged, ensure_ascii=False)

    except Exception as e:
        logger.error(f"Error in extract_workout_parameters: {e}", exc_info=True)
        # Return current params unchanged on error
        return current_params if current_params else json.dumps({
            "duration_minutes": None,
            "intensity": None,
            "workout_type": None,
            "genres": [],
            "all_collected": False
        })


def _extract_from_message(message: str) -> Dict[str, Any]:
    """
    Extract parameters from a single message using rule-based parsing.
    This is a helper function - the AI agent will use this through the tool.
    """
    import re

    params: Dict[str, Any] = {}
    message_lower = message.lower().strip()

    # Extract duration
    duration_patterns = [
        r'(\d+)\s*(?:хв|хвилин|minutes?|mins?)',
        r'(\d+\.?\d*)\s*(?:год|hours?)',
    ]

    for pattern in duration_patterns:
        match = re.search(pattern, message_lower)
        if match:
            value = float(match.group(1))
            unit = match.group(0).lower()

            if "год" in unit or "hour" in unit:
                params["duration_minutes"] = int(value * 60)
            else:
                params["duration_minutes"] = int(value)
            break

    # Extract intensity
    intensity_keywords = {
        "low": ["легк", "easy", "low", "recovery", "відновлювальн", "повільн", "спокійн"],
        "moderate": ["середн", "moderate", "темпов", "tempo", "звичайн", "нормальн"],
        "high": ["висок", "важк", "high", "hard", "інтенсивн", "intense", "швидк"],
    }

    for intensity, keywords in intensity_keywords.items():
        if any(keyword in message_lower for keyword in keywords):
            params["intensity"] = intensity
            break

    # Extract workout type
    workout_keywords = {
        "intervals": ["інтервал", "interval", "інтервальн"],
        "fartlek": ["фартлек", "fartlek"],
        "steady": ["біг", "пробіжк", "run", "running", "steady", "стабільн", "постійн", "темпов"],
    }

    for workout_type, keywords in workout_keywords.items():
        if any(keyword in message_lower for keyword in keywords):
            params["workout_type"] = workout_type
            break

    # Extract genres (normalize to English)
    genre_mapping = {
        "electronic": ["electronic", "electric", "electro", "електро", "електронн", "електронну", "електроніка", "edm", "едм"],
        "rock": ["rock", "рок"],
        "pop": ["pop", "поп"],
        "classical": ["classic", "classical", "класик", "класична", "класичну"],
        "hip-hop": ["hip-hop", "hip hop", "хіп-хоп", "rap", "реп"],
        "jazz": ["jazz", "джаз"],
        "metal": ["metal", "метал"],
        "indie": ["indie", "інді"],
        "alternative": ["alternative", "альтернатив"],
        "dance": ["dance", "данс"],
        "house": ["house", "хаус"],
        "techno": ["techno", "техно"],
        "trance": ["trance", "транс"],
        "reggae": ["reggae", "регі"],
        "country": ["country", "кантрі"],
        "blues": ["blues", "блюз"],
        "folk": ["folk", "фолк"],
        "ambient": ["ambient", "ембієнт", "chill", "релакс"],
        "r&b": ["r&b", "rnb"],
    }

    found_genres = []
    for genre, variations in genre_mapping.items():
        if any(var in message_lower for var in variations):
            found_genres.append(genre)

    if found_genres:
        params["genres"] = found_genres

    return params


def _merge_parameters(current: Dict[str, Any], extracted: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge extracted parameters with current parameters.
    Genres accumulate, other params update if not already set.
    """
    merged = current.copy()

    # Update duration, intensity, workout_type if extracted and not already set
    for key in ["duration_minutes", "intensity", "workout_type"]:
        if key in extracted and extracted[key] is not None:
            if key not in merged or merged[key] is None:
                merged[key] = extracted[key]

    # Accumulate genres (don't replace)
    if "genres" in extracted and extracted["genres"]:
        current_genres = merged.get("genres", [])
        if not isinstance(current_genres, list):
            current_genres = []

        # Add new genres to existing
        all_genres = list(set(current_genres + extracted["genres"]))
        merged["genres"] = all_genres
    elif "genres" not in merged:
        merged["genres"] = []

    return merged


def _check_all_collected(params: Dict[str, Any]) -> bool:
    """
    Check if all required parameters are collected.
    Required: duration_minutes, intensity, at least one genre
    """
    has_duration = params.get("duration_minutes") is not None
    has_intensity = params.get("intensity") is not None
    has_genres = bool(params.get("genres"))

    return has_duration and has_intensity and has_genres
