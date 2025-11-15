"""
Tests for WorkoutBuilder error handling.
"""
import pytest
from unittest.mock import AsyncMock, patch
from openai import RateLimitError, APITimeoutError, APIError

from app.services.workout_builder import WorkoutBuilder
from app.schemas.conversation import ConversationState
from app.utils.openai_error_handler import OpenAIErrorHandler


@pytest.fixture
def workout_builder():
    """Create WorkoutBuilder instance."""
    with patch('app.agents.base.ChatOpenAI'):
        builder = WorkoutBuilder()
        return builder


@pytest.fixture
def initial_state():
    """Create initial conversation state."""
    return ConversationState(user_id="test_user_123")


@pytest.mark.asyncio
async def test_workout_builder_rate_limit_error(workout_builder, initial_state):
    """Test that WorkoutBuilder handles rate limit errors gracefully."""
    # Mock rate limit error
    workout_builder.agent_executor.ainvoke = AsyncMock(
        side_effect=RateLimitError(
            message="Rate limit exceeded",
            response=None,
            body=None
        )
    )

    update = await workout_builder.process_message(initial_state, "привіт")

    # Should return user-friendly error message
    assert update.response_message is not None
    assert "перевантажений" in update.response_message.lower() or "спробуйте" in update.response_message.lower()
    assert len(update.new_state.history) == 2  # User message + error response


@pytest.mark.asyncio
async def test_workout_builder_timeout_error(workout_builder, initial_state):
    """Test that WorkoutBuilder handles timeout errors gracefully."""
    # Mock timeout error
    workout_builder.agent_executor.ainvoke = AsyncMock(
        side_effect=APITimeoutError(
            message="Request timed out",
            request=None
        )
    )

    update = await workout_builder.process_message(initial_state, "привіт")

    # Should return user-friendly error message
    assert update.response_message is not None
    assert "час" in update.response_message.lower() or "timeout" in update.response_message.lower()
    assert len(update.new_state.history) == 2


@pytest.mark.asyncio
async def test_workout_builder_api_error(workout_builder, initial_state):
    """Test that WorkoutBuilder handles generic API errors gracefully."""
    # Mock API error
    workout_builder.agent_executor.ainvoke = AsyncMock(
        side_effect=APIError(
            message="API error",
            request=None,
            body=None
        )
    )

    update = await workout_builder.process_message(initial_state, "привіт")

    # Should return user-friendly error message
    assert update.response_message is not None
    assert "помилк" in update.response_message.lower() or "error" in update.response_message.lower()
    assert len(update.new_state.history) == 2


@pytest.mark.asyncio
async def test_workout_builder_retry_on_rate_limit(workout_builder, initial_state):
    """Test that WorkoutBuilder retries on rate limit errors."""
    call_count = 0

    async def mock_ainvoke(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise RateLimitError(
                message="Rate limit exceeded",
                response=None,
                body=None
            )
        return {"output": "Привіт! Як можу допомогти?"}

    workout_builder.agent_executor.ainvoke = AsyncMock(side_effect=mock_ainvoke)

    # Mock sleep to speed up test
    with patch('asyncio.sleep', new_callable=AsyncMock):
        update = await workout_builder.process_message(initial_state, "привіт")

    # Should succeed after retry
    assert update.response_message is not None
    assert "привіт" in update.response_message.lower() or "допомогти" in update.response_message.lower()
    assert call_count == 2  # Should have retried once


@pytest.mark.asyncio
async def test_workout_builder_retry_on_timeout(workout_builder, initial_state):
    """Test that WorkoutBuilder retries on timeout errors."""
    call_count = 0

    async def mock_ainvoke(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise APITimeoutError(
                message="Request timed out",
                request=None
            )
        return {"output": "Привіт! Як можу допомогти?"}

    workout_builder.agent_executor.ainvoke = AsyncMock(side_effect=mock_ainvoke)

    # Mock sleep to speed up test
    with patch('asyncio.sleep', new_callable=AsyncMock):
        update = await workout_builder.process_message(initial_state, "привіт")

    # Should succeed after retry
    assert update.response_message is not None
    assert call_count == 2  # Should have retried once


@pytest.mark.asyncio
async def test_workout_builder_max_retries_exceeded(workout_builder, initial_state):
    """Test that WorkoutBuilder stops retrying after max attempts."""
    call_count = 0

    async def mock_ainvoke(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        raise RateLimitError(
            message="Rate limit exceeded",
            response=None,
            body=None
        )

    workout_builder.agent_executor.ainvoke = AsyncMock(side_effect=mock_ainvoke)

    # Mock sleep to speed up test
    with patch('asyncio.sleep', new_callable=AsyncMock):
        update = await workout_builder.process_message(initial_state, "привіт")

    # Should return error message after max retries
    assert update.response_message is not None
    assert "перевантажений" in update.response_message.lower() or "спробуйте" in update.response_message.lower()
    assert call_count == 3  # Should have tried 3 times (initial + 2 retries)


@pytest.mark.asyncio
async def test_workout_builder_non_api_error(workout_builder, initial_state):
    """Test that WorkoutBuilder handles non-API errors."""
    # Mock non-API error
    workout_builder.agent_executor.ainvoke = AsyncMock(
        side_effect=ValueError("Some other error")
    )

    update = await workout_builder.process_message(initial_state, "привіт")

    # Should return generic error message
    assert update.response_message is not None
    assert "помилк" in update.response_message.lower() or "error" in update.response_message.lower()
    assert len(update.new_state.history) == 2


@pytest.mark.asyncio
async def test_workout_builder_state_preserved_on_error(workout_builder, initial_state):
    """Test that conversation state is preserved when errors occur."""
    state = initial_state
    state.history.append({"role": "user", "content": "привіт"})
    state.history.append({"role": "assistant", "content": "Привіт!"})
    state.collected_parameters = {"duration_minutes": 30}

    workout_builder.agent_executor.ainvoke = AsyncMock(
        side_effect=RateLimitError(
            message="Rate limit exceeded",
            response=None,
            body=None
        )
    )

    update = await workout_builder.process_message(state, "30 хвилин")

    # State should be preserved
    assert len(update.new_state.history) > len(state.history)
    assert update.new_state.collected_parameters.get("duration_minutes") == 30
    assert update.new_state.user_id == state.user_id

