"""
Tools for workout parsing.
"""
from typing import Optional
from langchain.tools import tool
from loguru import logger

from app.schemas.llm_responses import WorkoutIntent
from app.services.parsers.rule_based_parser import RuleBasedParser


# Global parser instance
_rule_parser = RuleBasedParser()


@tool
def rule_based_parse(message: str) -> str:
    """
    Fast rule-based parsing for simple workout requests.

    Use this tool first for speed. Returns JSON string of WorkoutIntent
    if successful, or "None" if parsing failed.

    Args:
        message: User's workout request message

    Returns:
        JSON string of WorkoutIntent or "None"
    """
    try:
        result = _rule_parser.parse(message)
        if result:
            logger.info(f"Rule-based parsing successful for: {message[:50]}...")
            return result.model_dump_json()
        else:
            logger.debug(f"Rule-based parsing failed for: {message[:50]}...")
            return "None"
    except Exception as e:
        logger.error(f"Error in rule_based_parse: {e}")
        return "None"


@tool
def validate_intent(intent_json: str) -> str:
    """
    Validate workout intent completeness.

    Checks if intent has all required fields (duration, intensity, workout_type).

    Args:
        intent_json: JSON string of WorkoutIntent

    Returns:
        "valid" if complete, "invalid" with missing fields if incomplete
    """
    try:
        import json
        intent_dict = json.loads(intent_json)
        intent = WorkoutIntent(**intent_dict)

        missing_fields = []
        if not intent.duration_minutes or intent.duration_minutes < 5:
            missing_fields.append("duration_minutes")
        if not intent.target_bpm_min or not intent.target_bpm_max:
            missing_fields.append("target_bpm_min/max")
        if not intent.workout_type:
            missing_fields.append("workout_type")

        if missing_fields:
            return f"invalid: missing {', '.join(missing_fields)}"
        else:
            return "valid"
    except Exception as e:
        logger.error(f"Error validating intent: {e}")
        return f"invalid: {str(e)}"

