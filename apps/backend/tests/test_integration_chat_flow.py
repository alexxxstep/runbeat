"""
Integration tests for complete chat flow.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.agents.supervisor import SupervisorAgent
from app.schemas.conversation import ConversationState, ConversationUpdate


@pytest.fixture
def supervisor():
    """Create SupervisorAgent instance."""
    return SupervisorAgent()


@pytest.mark.asyncio
async def test_full_conversation_flow(supervisor):
    """Test complete conversation flow from greeting to workout creation."""
    with patch.object(
        supervisor.builder_service,
        'process_message',
        new_callable=AsyncMock
    ) as mock_process:
        # Step 1: Initial greeting
        mock_process.return_value = ConversationUpdate(
            new_state=ConversationState(user_id="test_user"),
            response_message="Привіт! Я допоможу тобі створити ідеальне тренування. Яку пробіжку ти хочеш зробити?"
        )

        response1 = await supervisor.handle_message("test_user", "привіт")
        assert "привіт" in response1.response_message.lower() or "тренування" in response1.response_message.lower()
        assert "test_user" in supervisor.states

        # Step 2: User provides workout details
        state2 = ConversationState(user_id="test_user")
        state2.collected_parameters = {"duration_minutes": 48, "intensity": "high"}
        mock_process.return_value = ConversationUpdate(
            new_state=state2,
            response_message="Чудово! Інтенсивна пробіжка на 48 хвилин. Яку музику ти хочеш слухати?"
        )

        response2 = await supervisor.handle_message("test_user", "інтенсивна пробіжка на 48 хвилин")
        assert "музик" in response2.response_message.lower() or "music" in response2.response_message.lower()
        assert supervisor.states["test_user"].collected_parameters.get("duration_minutes") == 48

        # Step 3: User provides music preferences
        state3 = ConversationState(user_id="test_user")
        state3.collected_parameters = {
            "duration_minutes": 48,
            "intensity": "high",
            "genres": ["rock"]
        }
        mock_process.return_value = ConversationUpdate(
            new_state=state3,
            response_message="Супер! Отже, інтенсивна пробіжка на 48 хвилин під рок. Створюємо воркаут?"
        )

        response3 = await supervisor.handle_message("test_user", "рок")
        assert "створ" in response3.response_message.lower() or "create" in response3.response_message.lower()
        assert supervisor.states["test_user"].collected_parameters.get("genres") == ["rock"]

        # Step 4: User confirms workout creation
        mock_process.return_value = ConversationUpdate(
            new_state=state3,
            response_message="✅ Воркаут успішно створено! Тепер ви можете згенерувати плейлист.",
            created_workout={"id": "test", "type": "steady", "duration_minutes": 30, "intensity": "moderate"},
            is_complete=True,
        )

        response4 = await supervisor.handle_message("test_user", "так")
        assert "✅" in response4.response_message or "створено" in response4.response_message.lower()
        # State should be cleared after successful creation
        assert "test_user" not in supervisor.states


@pytest.mark.asyncio
async def test_conversation_with_clarifications(supervisor):
    """Test conversation flow with clarifications."""
    with patch.object(
        supervisor.builder_service,
        'process_message',
        new_callable=AsyncMock
    ) as mock_process:
        # User provides incomplete info
        state1 = ConversationState(user_id="test_user")
        state1.collected_parameters = {"intensity": "high"}
        mock_process.return_value = ConversationUpdate(
            new_state=state1,
            response_message="Чудово! Інтенсивна пробіжка. Скільки часу плануєш бігти?"
        )

        response1 = await supervisor.handle_message("test_user", "інтенсивна пробіжка")
        assert "скільки" in response1.response_message.lower() or "how long" in response1.response_message.lower()
        assert "test_user" in supervisor.states

        # User provides duration
        state2 = ConversationState(user_id="test_user")
        state2.collected_parameters = {"duration_minutes": 30, "intensity": "high"}
        mock_process.return_value = ConversationUpdate(
            new_state=state2,
            response_message="Супер! Інтенсивна пробіжка на 30 хвилин. Яку музику ти хочеш слухати?"
        )

        response2 = await supervisor.handle_message("test_user", "30 хвилин")
        assert "музик" in response2.response_message.lower()
        assert supervisor.states["test_user"].collected_parameters.get("duration_minutes") == 30


@pytest.mark.asyncio
async def test_conversation_cancellation(supervisor):
    """Test conversation cancellation flow."""
    with patch.object(
        supervisor.builder_service,
        'process_message',
        new_callable=AsyncMock
    ) as mock_process:
        # User starts conversation
        mock_process.return_value = ConversationUpdate(
            new_state=ConversationState(user_id="test_user"),
            response_message="Привіт! Я допоможу тобі створити тренування."
        )

        await supervisor.handle_message("test_user", "привіт")
        assert "test_user" in supervisor.states

        # User cancels
        mock_process.return_value = ConversationUpdate(
            new_state=ConversationState(user_id="test_user"),
            response_message="Створення воркауту скасовано. Чим ще можу допомогти?"
        )

        response = await supervisor.handle_message("test_user", "ні")
        assert "скасовано" in response.response_message.lower() or "canceled" in response.response_message.lower()
        # State should be cleared after cancellation
        assert "test_user" not in supervisor.states


@pytest.mark.asyncio
async def test_conversation_error_recovery(supervisor):
    """Test conversation recovery after error."""
    with patch.object(
        supervisor.builder_service,
        'process_message',
        new_callable=AsyncMock
    ) as mock_process:
        # First message - error occurs
        mock_process.side_effect = Exception("Temporary error")

        with pytest.raises(Exception):
            await supervisor.handle_message("test_user", "привіт")

        # Second message - should recover
        mock_process.side_effect = None
        mock_process.return_value = ConversationUpdate(
            new_state=ConversationState(user_id="test_user"),
            response_message="Привіт! Я допоможу тобі створити тренування."
        )

        response = await supervisor.handle_message("test_user", "привіт")
        assert "привіт" in response.response_message.lower() or "допомогти" in response.response_message.lower()
        assert "test_user" in supervisor.states


@pytest.mark.asyncio
async def test_conversation_multiple_users(supervisor):
    """Test that supervisor handles multiple users independently."""
    with patch.object(
        supervisor.builder_service,
        'process_message',
        new_callable=AsyncMock
    ) as mock_process:
        mock_process.return_value = ConversationUpdate(
            new_state=ConversationState(user_id="user1"),
            response_message="Привіт!"
        )

        # User 1
        await supervisor.handle_message("user1", "привіт")
        assert "user1" in supervisor.states

        # User 2
        mock_process.return_value = ConversationUpdate(
            new_state=ConversationState(user_id="user2"),
            response_message="Hello!"
        )
        await supervisor.handle_message("user2", "hello")
        assert "user2" in supervisor.states

        # Both states should exist independently
        assert len(supervisor.states) == 2
        assert "user1" in supervisor.states
        assert "user2" in supervisor.states

