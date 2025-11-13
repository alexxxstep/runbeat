"""
Tests for playlist history endpoint.
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


@pytest.fixture
def mock_playlist_data():
    """Mock playlist data."""
    return {
        "id": "playlist_uuid",
        "user_id": "user_uuid",
        "workout_id": "workout_uuid",
        "spotify_playlist_id": "spotify_playlist_123",
        "spotify_url": "https://open.spotify.com/playlist/123",
        "tracks": [
            {"id": "track_1", "name": "Track 1"},
            {"id": "track_2", "name": "Track 2"},
        ],
        "total_duration_seconds": 1800,
        "generation_time_seconds": 8.5,
        "shared": False,
        "share_url": None,
        "created_at": "2025-11-12T10:00:00Z",
    }


@patch("app.api.routes.playlists.SupabaseService")
def test_get_playlist_history(mock_supabase_service, mock_playlist_data):
    """Test getting playlist history with workout data."""
    # Mock playlist with workout
    playlist_with_workout = mock_playlist_data.copy()
    playlist_with_workout["workouts"] = {
        "id": "workout_uuid",
        "type": "steady",
        "duration_minutes": 30,
        "intensity": "low",
        "hr_zones": [110, 130],
    }

    # Mock Supabase
    mock_supabase = MagicMock()
    mock_result = MagicMock()
    mock_result.data = [playlist_with_workout]
    mock_result.count = 1
    mock_supabase.get_client.return_value.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.offset.return_value.execute.return_value = (
        mock_result
    )
    mock_supabase_service.return_value = mock_supabase

    # Make request
    response = client.get(
        "/playlists/history?user_id=user_uuid&limit=10&offset=0"
    )

    assert response.status_code == 200
    data = response.json()
    assert "playlists" in data
    assert "total" in data
    assert len(data["playlists"]) == 1
    assert data["playlists"][0]["id"] == "playlist_uuid"
    assert data["playlists"][0]["total_tracks"] == 2
    assert data["playlists"][0]["spotify_url"] == "https://open.spotify.com/playlist/123"
    # Verify workout data is included
    if "workout" in data["playlists"][0]:
        assert data["playlists"][0]["workout"]["type"] == "steady"


@patch("app.api.routes.playlists.SupabaseService")
def test_get_playlist_history_empty(mock_supabase_service):
    """Test getting playlist history when empty."""
    # Mock Supabase
    mock_supabase = MagicMock()
    mock_result = MagicMock()
    mock_result.data = []
    mock_result.count = 0
    mock_supabase.get_client.return_value.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.offset.return_value.execute.return_value = (
        mock_result
    )
    mock_supabase_service.return_value = mock_supabase

    # Make request
    response = client.get(
        "/playlists/history?user_id=user_uuid&limit=10&offset=0"
    )

    assert response.status_code == 200
    data = response.json()
    assert "playlists" in data
    assert "total" in data
    assert len(data["playlists"]) == 0
    assert data["total"] == 0

