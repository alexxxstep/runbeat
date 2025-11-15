"""
Tests for OpenAI error handler utility.
"""
import pytest
from unittest.mock import AsyncMock, patch
from openai import RateLimitError, APITimeoutError, APIError, APIConnectionError

from app.utils.openai_error_handler import OpenAIErrorHandler


def test_is_rate_limit_error():
    """Test rate limit error detection."""
    assert OpenAIErrorHandler.is_rate_limit_error(
        RateLimitError(message="Rate limit", response=None, body=None)
    )
    assert OpenAIErrorHandler.is_rate_limit_error(Exception("rate_limit exceeded"))
    assert OpenAIErrorHandler.is_rate_limit_error(Exception("429 error"))
    assert OpenAIErrorHandler.is_rate_limit_error(Exception("quota exceeded"))
    assert not OpenAIErrorHandler.is_rate_limit_error(Exception("other error"))


def test_is_timeout_error():
    """Test timeout error detection."""
    assert OpenAIErrorHandler.is_timeout_error(
        APITimeoutError(message="Timeout", request=None)
    )
    assert OpenAIErrorHandler.is_timeout_error(
        APIConnectionError(message="Connection", request=None)
    )
    assert OpenAIErrorHandler.is_timeout_error(Exception("timeout occurred"))
    assert OpenAIErrorHandler.is_timeout_error(Exception("timed out"))
    assert not OpenAIErrorHandler.is_timeout_error(Exception("other error"))


def test_is_api_error():
    """Test API error detection."""
    assert OpenAIErrorHandler.is_api_error(
        RateLimitError(message="Rate limit", response=None, body=None)
    )
    assert OpenAIErrorHandler.is_api_error(
        APITimeoutError(message="Timeout", request=None)
    )
    assert OpenAIErrorHandler.is_api_error(
        APIError(message="API error", request=None, body=None)
    )
    assert not OpenAIErrorHandler.is_api_error(Exception("other error"))


def test_get_error_message_rate_limit():
    """Test error message for rate limit."""
    error = RateLimitError(message="Rate limit", response=None, body=None)
    message = OpenAIErrorHandler.get_error_message(error)
    assert "перевантажений" in message.lower() or "спробуйте" in message.lower()


def test_get_error_message_timeout():
    """Test error message for timeout."""
    error = APITimeoutError(message="Timeout", request=None)
    message = OpenAIErrorHandler.get_error_message(error)
    assert "час" in message.lower() or "timeout" in message.lower()


def test_get_error_message_api_error():
    """Test error message for API error."""
    error = APIError(message="API error", request=None, body=None)
    message = OpenAIErrorHandler.get_error_message(error)
    assert "помилк" in message.lower() or "error" in message.lower()


def test_get_error_message_generic():
    """Test error message for generic error."""
    error = ValueError("Some error")
    message = OpenAIErrorHandler.get_error_message(error)
    assert "помилк" in message.lower() or "error" in message.lower()


@pytest.mark.asyncio
async def test_handle_with_retry_success():
    """Test retry handler with successful call."""
    async def mock_func():
        return "success"

    result = await OpenAIErrorHandler.handle_with_retry(mock_func)
    assert result == "success"


@pytest.mark.asyncio
async def test_handle_with_retry_rate_limit_success():
    """Test retry handler with rate limit that succeeds on retry."""
    call_count = 0

    async def mock_func():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise RateLimitError(message="Rate limit", response=None, body=None)
        return "success"

    with patch('asyncio.sleep', new_callable=AsyncMock):
        result = await OpenAIErrorHandler.handle_with_retry(
            mock_func, max_retries=3, base_delay=0.1
        )
        assert result == "success"
        assert call_count == 2


@pytest.mark.asyncio
async def test_handle_with_retry_timeout_success():
    """Test retry handler with timeout that succeeds on retry."""
    call_count = 0

    async def mock_func():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise APITimeoutError(message="Timeout", request=None)
        return "success"

    with patch('asyncio.sleep', new_callable=AsyncMock):
        result = await OpenAIErrorHandler.handle_with_retry(
            mock_func, max_retries=3, base_delay=0.1
        )
        assert result == "success"
        assert call_count == 2


@pytest.mark.asyncio
async def test_handle_with_retry_max_retries():
    """Test retry handler stops after max retries."""
    call_count = 0

    async def mock_func():
        nonlocal call_count
        call_count += 1
        raise RateLimitError(message="Rate limit", response=None, body=None)

    with patch('asyncio.sleep', new_callable=AsyncMock):
        with pytest.raises(RateLimitError):
            await OpenAIErrorHandler.handle_with_retry(
                mock_func, max_retries=3, base_delay=0.1
            )
        assert call_count == 3  # Initial + 2 retries


@pytest.mark.asyncio
async def test_handle_with_retry_non_retryable_error():
    """Test retry handler doesn't retry non-retryable errors."""
    call_count = 0

    async def mock_func():
        nonlocal call_count
        call_count += 1
        raise ValueError("Non-retryable error")

    with pytest.raises(ValueError):
        await OpenAIErrorHandler.handle_with_retry(
            mock_func, max_retries=3
        )
    assert call_count == 1  # Should not retry

