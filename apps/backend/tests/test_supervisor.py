"""
Tests for SupervisorAgent.
"""
import pytest
from unittest.mock import AsyncMock, patch
from app.agents.supervisor import SupervisorAgent
from app.schemas.conversation import ConversationState, ConversationUpdate


@pytest.fixture
def supervisor():
    """Create SupervisorAgent instance."""
    return SupervisorAgent()


@pytest.fixture
def mock_workout_builder():
    """Mock WorkoutBuilder."""
    with patch('app.agents.supervisor.WorkoutBuilder') as mock_builder_class:
        mock_builder = AsyncMock()
        mock_builder_class.return_value = mock_builder
        yield mock_builder


@pytest.mark.asyncio
async def test_supervisor_initial_state_creation(supervisor):
    """Test that supervisor creates new state for new user."""
    with patch.object(
        supervisor.builder_service,
        'process_message',
        new_callable=AsyncMock
    ) as mock_process:
        mock_process.return_value = ConversationUpdate(
            new_state=ConversationState(user_id="test_user"),
            response_message="Привіт!"
        )

        response = await supervisor.handle_message("test_user", "привіт")

        assert response.response_message == "Привіт!"
        assert "test_user" in supervisor.states
        assert isinstance(supervisor.states["test_user"], ConversationState)


@pytest.mark.asyncio
async def test_supervisor_state_persistence(supervisor):
    """Test that supervisor maintains state between messages."""
    with patch.object(
        supervisor.builder_service,
        'process_message',
        new_callable=AsyncMock
    ) as mock_process:
        state1 = ConversationState(user_id="test_user")
        state1.history.append({"role": "user", "content": "привіт"})
        state1.history.append({"role": "assistant", "content": "Привіт!"})

        mock_process.return_value = ConversationUpdate(
            new_state=state1,
            response_message="Привіт!"
        )

        await supervisor.handle_message("test_user", "привіт")
        first_state = supervisor.states["test_user"]

        state2 = ConversationState(user_id="test_user")
        state2.history = state1.history.copy()
        state2.history.append({"role": "user", "content": "30 хвилин"})
        state2.history.append({"role": "assistant", "content": "Добре!"})

        mock_process.return_value = ConversationUpdate(
            new_state=state2,
            response_message="Добре!"
        )

        await supervisor.handle_message("test_user", "30 хвилин")
        second_state = supervisor.states["test_user"]

        assert len(second_state.history) > len(first_state.history)
        assert "test_user" in supervisor.states


@pytest.mark.asyncio
async def test_supervisor_state_clearing_on_success(supervisor):
    """Test that supervisor clears state after successful workout creation."""
    with patch.object(
        supervisor.builder_service,
        'process_message',
        new_callable=AsyncMock
    ) as mock_process:
        mock_process.return_value = ConversationUpdate(
            new_state=ConversationState(user_id="test_user"),
                response_message="✅ Воркаут успішно створено!",
                is_complete=True,
                created_workout={"id": "w1", "type": "steady", "duration_minutes": 30, "intensity": "low", "hr_zones": [110, 150]},
        )

        response = await supervisor.handle_message("test_user", "так")

        assert response.is_complete
        assert "test_user" not in supervisor.states


@pytest.mark.asyncio
async def test_supervisor_state_clearing_on_cancel(supervisor):
    """Test that supervisor clears state when user cancels."""
    with patch.object(
        supervisor.builder_service,
        'process_message',
        new_callable=AsyncMock
    ) as mock_process:
        mock_process.return_value = ConversationUpdate(
            new_state=ConversationState(user_id="test_user"),
            response_message="Створення воркауту скасовано"
        )

        response = await supervisor.handle_message("test_user", "ні")

        assert "test_user" not in supervisor.states
        assert "скасовано" in response.response_message.lower()


@pytest.mark.asyncio
async def test_supervisor_no_keyerror_after_clear(supervisor):
    """Test that supervisor doesn't raise KeyError after clearing state."""
    with patch.object(
        supervisor.builder_service,
        'process_message',
        new_callable=AsyncMock
    ) as mock_process:
        mock_process.return_value = ConversationUpdate(
            new_state=ConversationState(user_id="test_user"),
                response_message="✅ Воркаут успішно створено!",
                is_complete=True,
                created_workout={"id": "w2", "type": "steady", "duration_minutes": 30, "intensity": "low", "hr_zones": [110, 150]},
        )

        # Should not raise KeyError
        response = await supervisor.handle_message("test_user", "так")

        assert response.is_complete
        assert "test_user" not in supervisor.states


@pytest.mark.asyncio
async def test_supervisor_error_in_response_keeps_state(supervisor):
    """Test that supervisor keeps state if response contains error."""
    with patch.object(
        supervisor.builder_service,
        'process_message',
        new_callable=AsyncMock
    ) as mock_process:
        mock_process.return_value = ConversationUpdate(
            new_state=ConversationState(user_id="test_user"),
            response_message="✅ Воркаут створено, але error occurred"
        )

        await supervisor.handle_message("test_user", "так")

        # State should be kept because response contains "error"
        assert "test_user" in supervisor.states


def test_supervisor_invalid_user_id(supervisor):
    """Test that supervisor raises ValueError for invalid user_id."""
    with pytest.raises(ValueError, match="user_id must be a non-empty string"):
        supervisor._get_or_create_state("")

    with pytest.raises(ValueError, match="user_id must be a non-empty string"):
        supervisor._get_or_create_state(None)  # type: ignore

    with pytest.raises(ValueError, match="user_id must be a non-empty string"):
        supervisor._get_or_create_state("   ")  # Only whitespace


@pytest.mark.asyncio
async def test_supervisor_concurrent_requests(supervisor):
    """Test that supervisor handles concurrent requests from same user."""
    import asyncio

    with patch.object(
        supervisor.builder_service,
        'process_message',
        new_callable=AsyncMock
    ) as mock_process:
        mock_process.return_value = ConversationUpdate(
            new_state=ConversationState(user_id="test_user"),
            response_message="Відповідь"
        )

        # Simulate concurrent requests
        tasks = [
            supervisor.handle_message("test_user", f"message {i}")
            for i in range(5)
        ]

        responses = await asyncio.gather(*tasks)

        assert len(responses) == 5
        assert all(r.response_message == "Відповідь" for r in responses)
        # State should still exist (not cleared)
        assert "test_user" in supervisor.states

