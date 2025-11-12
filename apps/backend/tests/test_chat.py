"""
Tests for chat endpoints.
"""
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing."""
    return {
        "type": "steady",
        "duration_minutes": 30,
        "intensity": "low",
        "hr_zones": [110, 130],
        "confidence": 0.95,
        "needs_clarification": False,
    }


@pytest.fixture
def mock_llm_response_clarification():
    """Mock LLM response requiring clarification."""
    return {
        "type": "intervals",
        "duration_minutes": 40,
        "intensity": "moderate",
        "hr_zones": [130, 180],
        "confidence": 0.8,
        "needs_clarification": True,
        "clarification_question": "Який буде інтервал роботи/відпочинку?",
    }


@patch("app.api.routes.chat.LLMService")
def test_chat_message_success(mock_llm_service, mock_llm_response):
    """Test successful chat message parsing."""
    # Mock LLMService
    mock_service = AsyncMock()
    mock_service.parse_workout = AsyncMock(return_value=mock_llm_response)
    mock_llm_service.return_value = mock_service

    # Make request
    response = client.post(
        "/chat/message",
        json={"message": "Легке відновлення 30 хвилин"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Зрозумів! Генерую плейлист на 30 хв..."
    assert data["needs_clarification"] is False
    assert data["workout"] is not None
    assert data["workout"]["type"] == "steady"
    assert data["workout"]["duration_minutes"] == 30


@patch("app.api.routes.chat.LLMService")
def test_chat_message_clarification(mock_llm_service, mock_llm_response_clarification):
    """Test chat message requiring clarification."""
    # Mock LLMService
    mock_service = AsyncMock()
    mock_service.parse_workout = AsyncMock(
        return_value=mock_llm_response_clarification)
    mock_llm_service.return_value = mock_service

    # Make request
    response = client.post(
        "/chat/message",
        json={"message": "Хочу пробігти 40 хв з інтервалами"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["needs_clarification"] is True
    assert "Який буде інтервал" in data["message"]
    assert data["workout"] is None


def test_chat_message_empty():
    """Test chat message with empty message."""
    response = client.post(
        "/chat/message",
        json={"message": ""},
    )

    assert response.status_code == 422  # Validation error


def test_chat_message_missing_field():
    """Test chat message with missing message field."""
    response = client.post(
        "/chat/message",
        json={},
    )

    assert response.status_code == 422  # Validation error
