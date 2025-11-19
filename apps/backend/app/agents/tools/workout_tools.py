"""
Workout management tools for LangChain agents.
"""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from langchain.tools import tool
from loguru import logger

from app.services.supabase_service import supabase_service
from app.schemas.llm_responses import WorkoutIntent


# Genre normalization mapping (Ukrainian/variations → English)
GENRE_NORMALIZATION_MAP = {
    # Electronic and variants
    "електро": "electronic",
    "електронна": "electronic",
    "електронну": "electronic",
    "електроніка": "electronic",
    "електронн": "electronic",
    "electro": "electronic",
    "electric": "electronic",
    "едм": "electronic",
    "edm": "electronic",
    # Rock
    "рок": "rock",
    # Pop
    "поп": "pop",
    # Classical
    "класика": "classical",
    "класична": "classical",
    "класичну": "classical",
    "класик": "classical",
    # Hip-hop
    "хіп-хоп": "hip-hop",
    "hip hop": "hip-hop",
    "реп": "hip-hop",
    "rap": "hip-hop",
    # Metal
    "метал": "metal",
    # Techno
    "техно": "techno",
    # House
    "хаус": "house",
    # Jazz
    "джаз": "jazz",
    # Indie
    "інді": "indie",
    # Alternative
    "альтернатив": "alternative",
    # Dance
    "данс": "dance",
    # Trance
    "транс": "trance",
    # Reggae
    "регі": "reggae",
    # Country
    "кантрі": "country",
    # Blues
    "блюз": "blues",
    # Folk
    "фолк": "folk",
    # Ambient
    "ембієнт": "ambient",
    "chill": "ambient",
}


def _normalize_genre(genre: str) -> str:
    """
    Normalize genre name to English standard form.

    Args:
        genre: Genre name in any language/variant

    Returns:
        Normalized English genre name
    """
    genre_lower = genre.lower().strip()
    return GENRE_NORMALIZATION_MAP.get(genre_lower, genre_lower)


# Internal function (not a tool) - can be called directly
def _create_workout_from_params_internal(
    user_id: str,
    workout_type: str,
    duration_minutes: int,
    intensity: str,
    genres: Optional[str] = None,
    prompt: Optional[str] = None,
) -> str:
    """
    Internal function to create a workout in the database from simple parameters.
    This can be called directly by both tools and other services.

    Args:
        user_id: User ID
        workout_type: Workout type ("steady", "progressive", "intervals", "fartlek")
        duration_minutes: Duration in minutes (5-180)
        intensity: Intensity level ("low", "moderate", "high")
        genres: Optional comma-separated list of music genres (e.g., "rock,pop")
        prompt: Optional music prompt/description

    Returns:
        Workout ID if created successfully, "error: <message>" if failed
    """
    try:
        # Map intensity to BPM ranges
        intensity_to_bpm = {
            "low": [110, 130],
            "moderate": [130, 160],
            "high": [160, 180],
        }
        hr_zones = intensity_to_bpm.get(intensity, [120, 150])

        # Prepare workout data
        workout_data = {
            "user_id": user_id,
            "type": workout_type,
            "duration_minutes": duration_minutes,
            "intensity": intensity,
            "hr_zones": hr_zones,
        }

        # Add genres if provided (with normalization)
        if genres:
            genres_list = [g.strip() for g in genres.split(",") if g.strip()]
            if genres_list:
                # Normalize all genres to English
                normalized_genres = [_normalize_genre(g) for g in genres_list]
                # Remove duplicates while preserving order
                seen = set()
                unique_genres = []
                for g in normalized_genres:
                    if g not in seen:
                        seen.add(g)
                        unique_genres.append(g)
                workout_data["genres"] = unique_genres
                logger.debug(f"Normalized genres: {genres_list} → {unique_genres}")

        # Add prompt if provided
        if prompt:
            workout_data["prompt"] = prompt

        # Insert workout
        client = supabase_service.get_client()
        result = client.table("workouts").insert(workout_data).execute()

        if result.data and len(result.data) > 0:
            workout_obj = result.data[0]
            workout_id = workout_obj["id"]
            logger.info(f"Created workout {workout_id} for user {user_id} from conversation params")
            # Return workout_id|workout_json for parsing by supervisor
            import json

            return f"workout_created:{workout_id}|{json.dumps(workout_obj)}"
        else:
            return "error: Failed to create workout - no data returned"

    except Exception as e:
        logger.error(f"Error creating workout from params: {e}")
        return f"error: {str(e)}"


@tool
def create_workout(user_id: str, workout_intent_json: str) -> str:
    """
    Create a workout in the database from workout intent.

    Args:
        user_id: User ID
        workout_intent_json: JSON string of WorkoutIntent

    Returns:
        Workout ID if created successfully, "error: <message>" if failed
    """
    try:
        import json

        # datetime not needed - using supabase timestamps

        intent_dict = json.loads(workout_intent_json)
        workout_intent = WorkoutIntent(**intent_dict)

        client = supabase_service.get_client()

        # Map energy_profile to intensity
        if workout_intent.target_bpm_min < 120:
            intensity = "low"
        elif workout_intent.target_bpm_min < 150:
            intensity = "moderate"
        else:
            intensity = "high"

        # Map workout_type from WorkoutIntent to database type
        type_mapping = {
            "continuous": "steady",
            "intervals": "intervals",
            "fartlek": "fartlek",
            "recovery": "steady",
        }
        db_workout_type = type_mapping.get(workout_intent.workout_type, "steady")

        # Convert WorkoutIntent to workout data
        workout_data = {
            "user_id": user_id,
            "type": db_workout_type,
            "duration_minutes": workout_intent.duration_minutes,
            "intensity": intensity,
            "hr_zones": [workout_intent.target_bpm_min, workout_intent.target_bpm_max],
        }

        # Add optional fields
        if workout_intent.intervals:
            interval_stages = []
            for interval in workout_intent.intervals:
                interval_stages.append(
                    {
                        "name": getattr(interval, "name", "work"),
                        "duration_minutes": interval.duration_minutes,
                        "hr_zone": [workout_intent.target_bpm_min, workout_intent.target_bpm_max],
                        "bpm_range": [interval.target_bpm, interval.target_bpm],
                    }
                )
            workout_data["interval_stages"] = interval_stages

        # Add music preferences if provided
        if workout_intent.music_genres:
            workout_data["genres"] = workout_intent.music_genres
        if workout_intent.music_prompt:
            workout_data["prompt"] = workout_intent.music_prompt

        # Insert workout
        result = client.table("workouts").insert(workout_data).execute()

        if result.data and len(result.data) > 0:
            workout_id = result.data[0]["id"]
            logger.info(f"Created workout {workout_id} for user {user_id}")
            return workout_id
        else:
            return "error: Failed to create workout - no data returned"

    except Exception as e:
        logger.error(f"Error creating workout: {e}")
        return f"error: {str(e)}"


@tool
def activate_workout(workout_id: str, user_id: str) -> str:
    """
    Activate a workout for a user (set as active).

    Args:
        workout_id: Workout ID
        user_id: User ID (for security)

    Returns:
        "success" if activated, "error: <message>" if failed
    """
    try:
        client = supabase_service.get_client()

        # Try to activate workout (if is_active column exists)
        try:
            # First, deactivate all other workouts for this user
            client.table("workouts").update({"is_active": False}).eq("user_id", user_id).execute()

            # Activate the specified workout
            result = (
                client.table("workouts")
                .update({"is_active": True})
                .eq("id", workout_id)
                .eq("user_id", user_id)
                .execute()
            )

            if result.data and len(result.data) > 0:
                logger.info(f"Activated workout {workout_id} for user {user_id}")
                return "success"
            else:
                return "error: Workout not found or access denied"
        except Exception as e:
            error_dict = e if isinstance(e, dict) else {"code": None, "message": str(e)}
            # If column doesn't exist, just verify workout exists and return success
            if error_dict.get("code") == "42703" or "does not exist" in str(e).lower():
                logger.debug("is_active column does not exist, verifying workout exists")
                # Just verify the workout exists for this user
                result = (
                    client.table("workouts")
                    .select("id")
                    .eq("id", workout_id)
                    .eq("user_id", user_id)
                    .execute()
                )

                if result.data and len(result.data) > 0:
                    logger.info(
                        f"Workout {workout_id} exists for user {user_id} (is_active column not available)"
                    )
                    return "success"
                else:
                    return "error: Workout not found or access denied"
            else:
                raise  # Re-raise if it's a different error

    except Exception as e:
        logger.error(f"Error activating workout: {e}")
        return f"error: {str(e)}"


# Pydantic schema for tool arguments - explicitly marks duration and intensity as Optional
# This prevents LangChain from failing validation when agent calls tool without these params
class CreateWorkoutFromParamsInput(BaseModel):
    """Input schema for create_workout_from_params tool."""
    user_id: str = Field(..., description="User ID (required)")
    workout_type: str = Field(default="steady", description="Workout type: steady/intervals/fartlek")
    duration_minutes: Optional[int] = Field(default=None, description="Duration in minutes (5-180) - Optional in schema but required for creation")
    intensity: Optional[str] = Field(default=None, description="Intensity: low/moderate/high - Optional in schema but required for creation")
    genres: Optional[str] = Field(default=None, description="Comma-separated music genres (e.g., 'rock,pop')")
    prompt: Optional[str] = Field(default=None, description="Optional music prompt/description")

    model_config = ConfigDict(extra="allow")  # Pydantic V2 syntax - allow extra fields


@tool(args_schema=CreateWorkoutFromParamsInput)
def create_workout_from_params(
    user_id: str,
    workout_type: str = "steady",
    duration_minutes: Optional[int] = None,
    intensity: Optional[str] = None,
    genres: Optional[str] = None,
    prompt: Optional[str] = None,
    **kwargs  # Accept any extra kwargs to prevent validation errors
) -> str:
    """
    Create a workout in the database from simple parameters (for conversation flow).

    This is a simplified version that takes parameters directly from conversation state.

    IMPORTANT: This tool should ONLY be called when ALL required parameters are collected:
    - duration_minutes (required for creation, but Optional in schema to prevent validation errors)
    - intensity (required for creation, but Optional in schema to prevent validation errors)
    - At least one genre is recommended

    The agent should NOT call this tool until user has provided all information and confirmed.
    If called without required parameters, the tool will return an error message instead of crashing.

    Args:
        user_id (str): User ID (required)
        workout_type (str, optional): Workout type ("steady", "progressive", "intervals", "fartlek"). Defaults to "steady".
        duration_minutes (int, optional): Duration in minutes (5-180). Optional - will return error if None.
        intensity (str, optional): Intensity level ("low", "moderate", "high"). Optional - will return error if None.
        genres (str, optional): Comma-separated list of music genres (e.g., "rock,pop")
        prompt (str, optional): Optional music prompt/description
        **kwargs: Additional arguments (ignored)

    Returns:
        str: Workout ID if created successfully, "error: <message>" if failed
    """
    from loguru import logger

    # Log incoming parameters for debugging
    logger.debug(
        f"create_workout_from_params called: "
        f"user_id={user_id}, type={workout_type}, "
        f"duration={duration_minutes}, intensity={intensity}"
    )

    # Validate required parameters
    if duration_minutes is None:
        error_msg = (
            "error: duration_minutes is required. "
            "Please collect this information from the user first."
        )
        logger.warning(f"Validation failed: {error_msg}")
        return error_msg

    if intensity is None or intensity == "":
        error_msg = (
            "error: intensity is required. " "Please collect this information from the user first."
        )
        logger.warning(f"Validation failed: {error_msg}")
        return error_msg

    if duration_minutes < 5 or duration_minutes > 180:
        msg = f"error: duration_minutes must be between 5 and 180, " f"got {duration_minutes}"
        return msg

    if intensity not in ["low", "moderate", "high"]:
        msg = f"error: intensity must be 'low', 'moderate', or 'high', " f"got '{intensity}'"
        return msg

    # Call internal function
    return _create_workout_from_params_internal(
        user_id=user_id,
        workout_type=workout_type,
        duration_minutes=duration_minutes,
        intensity=intensity,
        genres=genres,
        prompt=prompt,
    )


@tool
def get_active_workout(user_id: str) -> str:
    """
    Get user's currently active workout.

    Args:
        user_id: User ID

    Returns:
        JSON string with workout data, or "none" if no active workout
    """
    try:
        import json

        client = supabase_service.get_client()

        # Try to get active workout (if is_active column exists)
        try:
            result = (
                client.table("workouts")
                .select("*")
                .eq("user_id", user_id)
                .eq("is_active", True)
                .execute()
            )

            if result.data and len(result.data) > 0:
                return json.dumps(result.data[0], default=str)
        except Exception as e:
            error_dict = e if isinstance(e, dict) else {"code": None, "message": str(e)}
            # If column doesn't exist, fallback to getting most recent workout
            if error_dict.get("code") == "42703" or "does not exist" in str(e).lower():
                logger.debug(
                    "is_active column does not exist, using most recent workout as fallback"
                )
                # Get most recent workout for user
                result = (
                    client.table("workouts")
                    .select("*")
                    .eq("user_id", user_id)
                    .order("created_at", desc=True)
                    .limit(1)
                    .execute()
                )

                if result.data and len(result.data) > 0:
                    return json.dumps(result.data[0], default=str)
            else:
                raise  # Re-raise if it's a different error

        return "none"

    except Exception as e:
        logger.error(f"Error getting active workout: {e}")
        return f"error: {str(e)}"
