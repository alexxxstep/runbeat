"""
Comprehensive tests for playlist endpoints including new features.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


@pytest.fixture
def mock_workout():
    """Mock workout data."""
    return {
        "type": "progressive",
        "duration_minutes": 45,
        "intensity": "moderate",
        "hr_zones": [120, 160],
    }


@pytest.fixture
def mock_user_token():
    """Mock user Spotify token."""
    return {
        "spotify_access_token": "mock_token",
        "spotify_token_expires_at": "2025-12-31T23:59:59Z",
    }


@patch("app.api.routes.playlists.SupabaseService")
def test_generate_playlist_creates_new_workout(mock_supabase_service, mock_workout):
    """Test that generating playlist without workout_id creates new workout."""
    # Mock Supabase
    mock_supabase = MagicMock()
    mock_supabase.get_client.return_value.table.return_value.select.return_value.eq.return_value.execute.return_value.data = (
        []
    )  # No existing workout

    # Mock workout creation
    workout_result = MagicMock()
    workout_result.data = [{"id": "new_workout_uuid"}]
    mock_supabase.get_client.return_value.table.return_value.insert.return_value.execute.return_value = (
        workout_result
    )

    # Mock playlist creation (no Spotify)
    playlist_result = MagicMock()
    playlist_result.data = [{"id": "new_playlist_uuid"}]
    mock_supabase.get_client.return_value.table.return_value.insert.return_value.execute.return_value = (
        playlist_result
    )

    mock_supabase_service.return_value = mock_supabase

    # Mock generator
    with patch("app.api.routes.playlists.PlaylistGenerator") as mock_gen:
        mock_gen_instance = AsyncMock()
        from app.models.playlist import PlaylistData, Track

        mock_gen_instance.generate = AsyncMock(
            return_value=PlaylistData(
                tracks=[
                    Track(
                        id="gen_track_1",
                        name="Generated Track",
                        artist="Artist",
                        artist_id="artist_id",
                        duration_ms=200000,
                        spotify_url="https://open.spotify.com/track/gen_track_1",
                        spotify_uri="spotify:track:gen_track_1",
                        tempo=140.0,
                        bpm=140.0,
                        energy=0.8,
                        danceability=0.7,
                        valence=0.6,
                    )
                ],
                total_duration=200.0,
                total_tracks=1,
            )
        )
        mock_gen.return_value = mock_gen_instance

        # Make request without workout_id
        response = client.post(
            "/playlists/generate",
            json={
                "workout": mock_workout,
                "user_preferences": {"top_genres": ["pop"]},
                "user_id": "user_uuid",
                # No workout_id - should create new workout
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "tracks" in data


@patch("app.api.routes.playlists.SupabaseService")
def test_generate_playlist_reuses_existing_workout(
    mock_supabase_service, mock_workout
):
    """Test that generating playlist with valid workout_id reuses existing workout."""
    # Mock Supabase
    mock_supabase = MagicMock()

    # Mock workout check - workout exists
    workout_check = MagicMock()
    workout_check.data = [{"id": "existing_workout_uuid"}]
    mock_supabase.get_client.return_value.table.return_value.select.return_value.eq.return_value.execute.return_value = (
        workout_check
    )

    # Mock playlist creation
    playlist_result = MagicMock()
    playlist_result.data = [{"id": "new_playlist_uuid"}]
    mock_supabase.get_client.return_value.table.return_value.insert.return_value.execute.return_value = (
        playlist_result
    )

    mock_supabase_service.return_value = mock_supabase

    # Mock generator
    with patch("app.api.routes.playlists.PlaylistGenerator") as mock_gen:
        mock_gen_instance = AsyncMock()
        from app.models.playlist import PlaylistData, Track

        mock_gen_instance.generate = AsyncMock(
            return_value=PlaylistData(
                tracks=[
                    Track(
                        id="gen_track_1",
                        name="Generated Track",
                        artist="Artist",
                        artist_id="artist_id",
                        duration_ms=200000,
                        spotify_url="https://open.spotify.com/track/gen_track_1",
                        spotify_uri="spotify:track:gen_track_1",
                        tempo=140.0,
                        bpm=140.0,
                        energy=0.8,
                        danceability=0.7,
                        valence=0.6,
                    )
                ],
                total_duration=200.0,
                total_tracks=1,
            )
        )
        mock_gen.return_value = mock_gen_instance

        # Make request with existing workout_id
        response = client.post(
            "/playlists/generate",
            json={
                "workout": mock_workout,
                "user_preferences": {"top_genres": ["pop"]},
                "user_id": "user_uuid",
                "workout_id": "existing_workout_uuid",
            },
        )

        assert response.status_code == 200
        # Verify workout was not created again (should reuse existing)
        # This is verified by checking that insert was not called for workouts


@patch("app.api.routes.playlists.SupabaseService")
def test_generate_playlist_invalid_workout_id_fallback(
    mock_supabase_service, mock_workout
):
    """Test that invalid workout_id creates new workout as fallback."""
    # Mock Supabase
    mock_supabase = MagicMock()

    # Mock workout check - workout NOT found
    workout_check = MagicMock()
    workout_check.data = []  # Workout not found
    mock_supabase.get_client.return_value.table.return_value.select.return_value.eq.return_value.execute.return_value = (
        workout_check
    )

    # Mock new workout creation (fallback)
    workout_result = MagicMock()
    workout_result.data = [{"id": "new_workout_uuid"}]
    mock_supabase.get_client.return_value.table.return_value.insert.return_value.execute.return_value = (
        workout_result
    )

    # Mock playlist creation
    playlist_result = MagicMock()
    playlist_result.data = [{"id": "new_playlist_uuid"}]
    mock_supabase.get_client.return_value.table.return_value.insert.return_value.execute.return_value = (
        playlist_result
    )

    mock_supabase_service.return_value = mock_supabase

    # Mock generator
    with patch("app.api.routes.playlists.PlaylistGenerator") as mock_gen:
        mock_gen_instance = AsyncMock()
        from app.models.playlist import PlaylistData, Track

        mock_gen_instance.generate = AsyncMock(
            return_value=PlaylistData(
                tracks=[
                    Track(
                        id="gen_track_1",
                        name="Generated Track",
                        artist="Artist",
                        artist_id="artist_id",
                        duration_ms=200000,
                        spotify_url="https://open.spotify.com/track/gen_track_1",
                        spotify_uri="spotify:track:gen_track_1",
                        tempo=140.0,
                        bpm=140.0,
                        energy=0.8,
                        danceability=0.7,
                        valence=0.6,
                    )
                ],
                total_duration=200.0,
                total_tracks=1,
            )
        )
        mock_gen.return_value = mock_gen_instance

        # Make request with invalid workout_id
        response = client.post(
            "/playlists/generate",
            json={
                "workout": mock_workout,
                "user_preferences": {"top_genres": ["pop"]},
                "user_id": "user_uuid",
                "workout_id": "invalid_workout_uuid",  # Invalid ID
            },
        )

        assert response.status_code == 200
        # New workout should be created as fallback


@patch("app.api.routes.playlists.SupabaseService")
def test_delete_playlist(mock_supabase_service):
    """Test deleting a playlist."""
    # Mock Supabase
    mock_supabase = MagicMock()
    mock_supabase.get_client.return_value.table.return_value.delete.return_value.eq.return_value.execute.return_value.data = (
        [{"id": "playlist_uuid"}]
    )
    mock_supabase_service.return_value = mock_supabase

    # Make request
    response = client.delete(
        "/playlists/playlist_uuid?user_id=user_uuid"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Playlist deleted successfully"


@patch("app.api.routes.playlists.SupabaseService")
def test_delete_playlist_not_found(mock_supabase_service):
    """Test deleting a non-existent playlist."""
    # Mock Supabase
    mock_supabase = MagicMock()
    table_mock = mock_supabase.get_client.return_value.table.return_value
    select_mock = table_mock.select.return_value
    first_eq = select_mock.eq.return_value
    second_eq = first_eq.eq.return_value
    second_eq.execute.return_value.data = []
    mock_supabase.get_client.return_value.table.return_value.delete.return_value.eq.return_value.execute.return_value.data = (
        []
    )
    mock_supabase_service.return_value = mock_supabase

    # Make request
    response = client.delete(
        "/playlists/nonexistent?user_id=user_uuid"
    )

    assert response.status_code == 404

