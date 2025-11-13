"""
Tests for playlist generation endpoints with selected tracks support.
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
        "type": "steady",
        "duration_minutes": 30,
        "intensity": "low",
        "hr_zones": [110, 130],
    }


@pytest.fixture
def mock_selected_tracks():
    """Mock selected tracks from variant."""
    return [
        {
            "id": "track_1",
            "name": "Test Track 1",
            "artist": "Test Artist 1",
            "artist_id": "artist_1",
            "duration_ms": 200000,
            "spotify_uri": "spotify:track:track_1",
            "spotify_url": "https://open.spotify.com/track/track_1",
            "preview_url": None,
            "external_urls": {"spotify": "https://open.spotify.com/track/track_1"},
            "album": "Test Album 1",
            "tempo": 140.0,
            "bpm": 140.0,
            "energy": 0.8,
            "danceability": 0.7,
            "valence": 0.6,
            "genres": ["pop"],
        },
        {
            "id": "track_2",
            "name": "Test Track 2",
            "artist": "Test Artist 2",
            "artist_id": "artist_2",
            "duration_ms": 180000,
            "spotify_uri": "spotify:track:track_2",
            "spotify_url": "https://open.spotify.com/track/track_2",
            "preview_url": None,
            "external_urls": {"spotify": "https://open.spotify.com/track/track_2"},
            "album": "Test Album 2",
            "tempo": 135.0,
            "bpm": 135.0,
            "energy": 0.75,
            "danceability": 0.65,
            "valence": 0.55,
            "genres": ["rock"],
        },
    ]


@patch("app.api.routes.playlists.PlaylistGenerator")
@patch("app.api.routes.playlists.SpotifyService")
@patch("app.api.routes.playlists.SupabaseService")
def test_generate_playlist_with_selected_tracks(
    mock_supabase_service,
    mock_spotify_service,
    mock_generator,
    mock_workout,
    mock_selected_tracks,
):
    """Test playlist generation with pre-selected tracks from variant."""
    # Mock Supabase
    mock_supabase = MagicMock()
    mock_supabase.get_client.return_value.table.return_value.select.return_value.eq.return_value.execute.return_value.data = (
        []  # No existing user token
    )
    mock_supabase.get_client.return_value.table.return_value.insert.return_value.execute.return_value.data = [
        {"id": "workout_uuid"}
    ]
    mock_supabase_service.return_value = mock_supabase

    # Make request with selected tracks
    response = client.post(
        "/playlists/generate",
        json={
            "workout": mock_workout,
            "user_preferences": {"top_genres": ["pop", "rock"]},
            "user_id": "user_uuid",
            "selected_tracks": mock_selected_tracks,
        },
    )

    # Should return tracks without generating new ones
    assert response.status_code == 200
    data = response.json()
    assert "tracks" in data
    assert len(data["tracks"]) == 2
    assert data["total_tracks"] == 2
    assert data["tracks"][0]["id"] == "track_1"
    assert data["tracks"][1]["id"] == "track_2"


@patch("app.api.routes.playlists.PlaylistGenerator")
@patch("app.api.routes.playlists.SpotifyService")
@patch("app.api.routes.playlists.SupabaseService")
def test_generate_playlist_with_workout_id(
    mock_supabase_service,
    mock_spotify_service,
    mock_generator,
    mock_workout,
):
    """Test playlist generation with existing workout_id."""
    # Mock Supabase
    mock_supabase = MagicMock()
    mock_supabase.get_client.return_value.table.return_value.select.return_value.eq.return_value.execute.return_value.data = (
        [{"id": "workout_uuid"}]  # Existing workout found
    )
    mock_supabase.get_client.return_value.table.return_value.insert.return_value.execute.return_value.data = [
        {"id": "playlist_uuid"}
    ]
    mock_supabase_service.return_value = mock_supabase

    # Mock generator
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
    mock_generator.return_value = mock_gen_instance

    # Make request with workout_id
    response = client.post(
        "/playlists/generate",
        json={
            "workout": mock_workout,
            "user_preferences": {"top_genres": ["pop"]},
            "user_id": "user_uuid",
            "workout_id": "workout_uuid",  # Existing workout ID
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "tracks" in data


@patch("app.api.routes.playlists.PlaylistGenerator")
def test_preview_playlist_variants_with_excluded_tracks(
    mock_generator, mock_workout
):
    """Test preview variants with excluded track IDs."""
    # Mock generator
    mock_gen_instance = AsyncMock()
    from app.models.playlist import PlaylistData, Track

    mock_gen_instance.generate = AsyncMock(
        return_value=PlaylistData(
            tracks=[
                Track(
                    id="variant_track_1",
                    name="Variant Track 1",
                    artist="Artist 1",
                    artist_id="artist_1",
                    duration_ms=200000,
                    spotify_url="https://open.spotify.com/track/variant_track_1",
                    spotify_uri="spotify:track:variant_track_1",
                    tempo=140.0,
                    bpm=140.0,
                    energy=0.8,
                    danceability=0.7,
                    valence=0.6,
                ),
                Track(
                    id="variant_track_2",
                    name="Variant Track 2",
                    artist="Artist 2",
                    artist_id="artist_2",
                    duration_ms=180000,
                    spotify_url="https://open.spotify.com/track/variant_track_2",
                    spotify_uri="spotify:track:variant_track_2",
                    tempo=135.0,
                    bpm=135.0,
                    energy=0.75,
                    danceability=0.65,
                    valence=0.55,
                ),
            ],
            total_duration=380.0,
            total_tracks=2,
        )
    )
    mock_generator.return_value = mock_gen_instance

    # Make request with excluded tracks
    response = client.post(
        "/playlists/preview-variants",
        json={
            "workout": mock_workout,
            "user_preferences": {"top_genres": ["pop", "rock"]},
            "user_id": "user_uuid",
            "excluded_track_ids": ["excluded_track_1", "excluded_track_2"],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "variant1" in data
    assert "variant2" in data
    assert "generation_time_seconds" in data

    # Verify generator was called with excluded_track_ids
    calls = mock_gen_instance.generate.call_args_list
    assert len(calls) >= 1
    # Check that excluded_track_ids was passed
    for call in calls:
        assert "excluded_track_ids" in call.kwargs


@patch("app.api.routes.playlists.PlaylistGenerator")
def test_preview_variants_duration_validation(mock_generator, mock_workout):
    """Test that variants have duration longer than workout duration."""
    # Mock generator
    mock_gen_instance = AsyncMock()
    from app.models.playlist import PlaylistData, Track

    # Create tracks that total more than 30 minutes (1800 seconds)
    tracks_count = 20
    track_duration_ms = 200000  # 200 seconds per track
    mock_gen_instance.generate = AsyncMock(
        return_value=PlaylistData(
            tracks=[
                Track(
                    id=f"track_{i}",
                    name=f"Track {i}",
                    artist=f"Artist {i}",
                    artist_id=f"artist_{i}",
                    duration_ms=track_duration_ms,
                    spotify_url=f"https://open.spotify.com/track/track_{i}",
                    spotify_uri=f"spotify:track:track_{i}",
                    tempo=140.0,
                    bpm=140.0,
                    energy=0.8,
                    danceability=0.7,
                    valence=0.6,
                )
                for i in range(tracks_count)
            ],
            total_duration=track_duration_ms * tracks_count / 1000,  # 4000 seconds
            total_tracks=tracks_count,
        )
    )
    mock_generator.return_value = mock_gen_instance

    # Make request
    response = client.post(
        "/playlists/preview-variants",
        json={
            "workout": mock_workout,  # 30 minutes workout
            "user_preferences": {"top_genres": ["pop"]},
            "user_id": "user_uuid",
        },
    )

    assert response.status_code == 200
    data = response.json()

    # Verify both variants have duration >= workout duration (30 min = 1800 sec)
    variant1_duration = data["variant1"]["total_duration"]
    variant2_duration = data["variant2"]["total_duration"]
    workout_duration_seconds = mock_workout["duration_minutes"] * 60

    assert variant1_duration >= workout_duration_seconds
    assert variant2_duration >= workout_duration_seconds

