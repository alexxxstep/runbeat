"""
Utility for handling OpenAI API errors with retry logic and fallbacks.
"""
import asyncio
from typing import Optional, Callable, Any
from loguru import logger

from openai import RateLimitError, APITimeoutError, APIError, APIConnectionError


class OpenAIErrorHandler:
    """Handler for OpenAI API errors with retry and fallback logic."""

    @staticmethod
    def is_rate_limit_error(error: Exception) -> bool:
        """Check if error is a rate limit error."""
        error_str = str(error).lower()
        return (
            isinstance(error, RateLimitError)
            or "rate_limit" in error_str
            or "429" in error_str
            or "rate limit" in error_str
            or "quota" in error_str
        )

    @staticmethod
    def is_timeout_error(error: Exception) -> bool:
        """Check if error is a timeout error."""
        error_str = str(error).lower()
        return (
            isinstance(error, APITimeoutError)
            or isinstance(error, APIConnectionError)
            or "timeout" in error_str
            or "timed out" in error_str
            or "connection" in error_str
        )

    @staticmethod
    def is_api_error(error: Exception) -> bool:
        """Check if error is an OpenAI API error."""
        return isinstance(error, (RateLimitError, APITimeoutError, APIError, APIConnectionError))

    @staticmethod
    async def handle_with_retry(
        func: Callable,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 10.0,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute function with retry logic for rate limits and timeouts.

        Args:
            func: Async function to execute
            max_retries: Maximum number of retries
            base_delay: Base delay in seconds for exponential backoff
            max_delay: Maximum delay in seconds
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result from func

        Raises:
            Exception: If all retries fail
        """
        last_error = None

        for attempt in range(max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_error = e

                if OpenAIErrorHandler.is_rate_limit_error(e):
                    if attempt < max_retries - 1:
                        # Exponential backoff with jitter
                        delay = min(
                            base_delay * (2 ** attempt),
                            max_delay
                        )
                        logger.warning(
                            f"Rate limit error (attempt {attempt + 1}/{max_retries}), "
                            f"retrying in {delay:.1f}s"
                        )
                        await asyncio.sleep(delay)
                        continue
                    else:
                        logger.error(
                            f"Rate limit error after {max_retries} attempts"
                        )
                        raise

                elif OpenAIErrorHandler.is_timeout_error(e):
                    if attempt < max_retries - 1:
                        delay = min(base_delay * (attempt + 1), max_delay)
                        logger.warning(
                            f"Timeout error (attempt {attempt + 1}/{max_retries}), "
                            f"retrying in {delay:.1f}s"
                        )
                        await asyncio.sleep(delay)
                        continue
                    else:
                        logger.error(
                            f"Timeout error after {max_retries} attempts"
                        )
                        raise

                else:
                    # Non-retryable error
                    raise

        # Should not reach here, but just in case
        if last_error:
            raise last_error

    @staticmethod
    def get_error_message(error: Exception) -> str:
        """
        Get user-friendly error message for OpenAI errors.

        Args:
            error: Exception to process

        Returns:
            User-friendly error message
        """
        if OpenAIErrorHandler.is_rate_limit_error(error):
            return (
                "Наразі сервіс перевантажений запитами. "
                "Будь ласка, спробуйте через кілька секунд."
            )
        elif OpenAIErrorHandler.is_timeout_error(error):
            return (
                "Час очікування вичерпано. "
                "Перевірте підключення до інтернету та спробуйте ще раз."
            )
        elif isinstance(error, APIError):
            return (
                "Виникла помилка при обробці запиту. "
                "Спробуйте ще раз або зверніться до підтримки."
            )
        else:
            return "Вибачте, виникла несподівана помилка. Спробуйте ще раз."

