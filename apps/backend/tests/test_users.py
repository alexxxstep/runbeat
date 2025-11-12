"""
Tests for user preferences endpoints.
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


@pytest.fixture
def mock_user_data():
    """Mock user data."""
    return {
        "id": "user_uuid",
        "preferences": {
            "top_genres": ["pop", "rock"],
            "top_artists": ["artist_1", "artist_2"],
            "avg_bpm": 145,
        },
    }


@patch("app.api.routes.users.SupabaseService")
def test_get_user_preferences(mock_supabase_service, mock_user_data):
    """Test getting user preferences."""
    # Mock Supabase
    mock_supabase = MagicMock()
    mock_supabase.get_client.return_value.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        mock_user_data
    ]
    mock_supabase_service.return_value = mock_supabase

    # Make request
    response = client.get("/users/user_uuid/preferences")

    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "user_uuid"
    assert "preferences" in data
    assert data["preferences"]["top_genres"] == ["pop", "rock"]
    assert data["preferences"]["avg_bpm"] == 145


@patch("app.api.routes.users.SupabaseService")
def test_get_user_preferences_not_found(mock_supabase_service):
    """Test getting preferences for non-existent user."""
    # Mock Supabase
    mock_supabase = MagicMock()
    mock_supabase.get_client.return_value.table.return_value.select.return_value.eq.return_value.execute.return_value.data = (
        []
    )
    mock_supabase_service.return_value = mock_supabase

    # Make request
    response = client.get("/users/nonexistent/preferences")

    assert response.status_code == 404


@patch("app.api.routes.users.SupabaseService")
def test_update_user_preferences(mock_supabase_service, mock_user_data):
    """Test updating user preferences."""
    # Mock Supabase
    updated_user = mock_user_data.copy()
    updated_user["preferences"]["avg_bpm"] = 150
    updated_user["preferences"]["top_genres"] = ["pop", "rock", "electronic"]

    mock_supabase = MagicMock()
    mock_supabase.get_client.return_value.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [
        updated_user
    ]
    mock_supabase_service.return_value = mock_supabase

    # Make request
    response = client.put(
        "/users/user_uuid/preferences",
        json={
            "preferences": {
                "top_genres": ["pop", "rock", "electronic"],
                "top_artists": ["artist_1", "artist_2"],
                "avg_bpm": 150,
            }
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "user_uuid"
    assert data["preferences"]["avg_bpm"] == 150
    assert len(data["preferences"]["top_genres"]) == 3


@patch("app.api.routes.users.SupabaseService")
def test_update_user_preferences_not_found(mock_supabase_service):
    """Test updating preferences for non-existent user."""
    # Mock Supabase
    mock_supabase = MagicMock()
    mock_supabase.get_client.return_value.table.return_value.update.return_value.eq.return_value.execute.return_value.data = (
        []
    )
    mock_supabase_service.return_value = mock_supabase

    # Make request
    response = client.put(
        "/users/nonexistent/preferences",
        json={
            "preferences": {
                "top_genres": ["pop"],
                "top_artists": [],
                "avg_bpm": 145,
            }
        },
    )

    assert response.status_code == 404

