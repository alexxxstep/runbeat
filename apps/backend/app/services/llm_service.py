"""
LLM Service for OpenAI GPT-4 integration.
"""
from openai import AsyncOpenAI
from app.core.config import settings
from loguru import logger
import json
from typing import Dict, Any


class LLMService:
    """Service for interacting with OpenAI GPT-4."""

    def __init__(self):
        """Initialize OpenAI client."""
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        logger.info(f"LLMService initialized with model: {settings.OPENAI_MODEL}")

    async def parse_workout(self, prompt: str) -> Dict[str, Any]:
        """
        Parse workout intent using GPT-4.

        Args:
            prompt: The prompt to send to GPT-4

        Returns:
            Dictionary with parsed workout parameters

        Raises:
            Exception: If OpenAI API call fails or parsing fails
        """
        try:
            response = await self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a JSON-only assistant. Return only valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,  # Lower for more consistent parsing
                max_tokens=500,
            )

            content = response.choices[0].message.content

            if not content:
                raise ValueError("Empty response from OpenAI")

            # Strip markdown if present
            if content.startswith("```json"):
                content = content.replace("```json\n", "").replace("```\n", "").replace("```", "")
            elif content.startswith("```"):
                content = content.replace("```\n", "").replace("```", "")

            # Parse JSON
            parsed = json.loads(content.strip())
            logger.debug(f"Parsed workout: {parsed}")
            return parsed

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from OpenAI response: {e}")
            logger.error(f"Response content: {content}")
            raise ValueError(f"Invalid JSON response from OpenAI: {e}")
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise

