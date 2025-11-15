"""
Tests for chat endpoints.
"""
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


@patch("app.api.routes.chat.supervisor_agent")
def test_chat_message_success(mock_supervisor):
    """Test successful chat message processing via supervisor agent."""
    mock_supervisor.handle_message = AsyncMock(return_value="Асистент: все зрозуміло.")

    response = client.post(
        "/chat/message",
        json={"message": "Легке відновлення 30 хвилин", "user_id": "user_123"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Асистент: все зрозуміло."
    assert data["needs_clarification"] is False
    assert data["workout"] is None
    mock_supervisor.handle_message.assert_awaited_once()


@patch("app.api.routes.chat.supervisor_agent")
def test_chat_message_error_handling(mock_supervisor):
    """Ensure server error propagates when supervisor fails."""
    mock_supervisor.handle_message = AsyncMock(side_effect=RuntimeError("boom"))

    response = client.post(
        "/chat/message",
        json={"message": "Помилка?", "user_id": "user_123"},
    )

    assert response.status_code == 500


def test_chat_message_empty():
    """Test chat message with empty message."""
    response = client.post(
        "/chat/message",
        json={"message": "", "user_id": "user_123"},
    )

    assert response.status_code == 422  # Validation error


def test_chat_message_missing_field():
    """Test chat message with missing message field."""
    response = client.post(
        "/chat/message",
        json={"user_id": "user_123"},
    )

    assert response.status_code == 422  # Validation error


def test_chat_message_missing_user_id():
    """Request without user_id should fail with 400."""
    response = client.post(
        "/chat/message",
        json={"message": "Привіт"},
    )

    assert response.status_code == 400
