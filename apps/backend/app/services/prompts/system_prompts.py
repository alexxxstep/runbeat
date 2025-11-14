"""
Base system prompts for RunBeat LLM service.
"""
from typing import Literal

# Base system prompt for JSON-only responses
BASE_SYSTEM_PROMPT = """You are a JSON-only assistant. Return only valid JSON without markdown formatting."""

# Response format types
ResponseFormat = Literal["json", "structured", "conversational"]

# Prompt version for A/B testing
PROMPT_VERSION = "v1.0"

