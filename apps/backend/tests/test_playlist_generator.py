"""
Tests for playlist generator.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.playlist_generator import PlaylistGenerator
from app.services.spotify_service import SpotifyService
from app.models.workout import Workout


@pytest.fixture
def mock_spotify_service():
    """Mock SpotifyService."""
    return MagicMock(spec=SpotifyService)


@pytest.fixture
def mock_spotify_track():
    """Mock Spotify track data."""
    return {
        "id": "test_track_id",
        "name": "Test Track",
        "artists": [{"id": "test_artist_id", "name": "Test Artist"}],
        "album": {"name": "Test Album"},
        "duration_ms": 200000,  # 200 seconds
        "external_urls": {"spotify": "https://open.spotify.com/track/test"},
        "uri": "spotify:track:test",
        "preview_url": "https://preview.url",
        "tempo": 140.0,
        "energy": 0.8,
        "danceability": 0.7,
        "valence": 0.6,
    }


@pytest.fixture
def workout_steady():
    """Steady workout fixture."""
    return Workout(
        type="steady",
        duration_minutes=30,
        intensity="low",
        hr_zones=[110, 130],
        confidence=0.95,
        needs_clarification=False,
    )


@pytest.fixture
def user_preferences():
    """User preferences fixture."""
    return {
        "top_genres": ["pop", "rock"],
        "top_artists": ["artist_1", "artist_2"],
        "avg_bpm": 145,
    }


async def test_generate_playlist_steady(
    mock_spotify_service, workout_steady, user_preferences, mock_spotify_track
):
    """Test playlist generation for steady workout."""
    # Setup mocks
    mock_spotify_service.get_recommendations = AsyncMock(
        return_value=[mock_spotify_track] * 5
    )

    generator = PlaylistGenerator(mock_spotify_service)

    result = await generator.generate(workout_steady, user_preferences)

    assert result.total_tracks > 0
    assert result.total_duration > 0
    assert len(result.tracks) == result.total_tracks


def test_calculate_target_bpm(mock_spotify_service):
    """Test BPM calculation from intensity."""
    generator = PlaylistGenerator(mock_spotify_service)

    assert generator._calculate_target_bpm("low") == 125
    assert generator._calculate_target_bpm("moderate") == 145
    assert generator._calculate_target_bpm("high") == 165
    assert generator._calculate_target_bpm("unknown") == 145  # Default


def test_create_segments_steady(mock_spotify_service, workout_steady):
    """Test segment creation for steady workout."""
    generator = PlaylistGenerator(mock_spotify_service)

    segments = generator._create_segments(workout_steady)

    assert len(segments) == 3
    assert segments[0]["name"] == "warm-up"
    assert segments[1]["name"] == "main"
    assert segments[2]["name"] == "cool-down"


def test_create_segments_progressive(mock_spotify_service):
    """Test segment creation for progressive workout."""
    generator = PlaylistGenerator(mock_spotify_service)

    workout = Workout(
        type="progressive",
        duration_minutes=45,
        intensity="moderate",
        hr_zones=[120, 160],
    )

    segments = generator._create_segments(workout)

    assert len(segments) == 5
    assert all("segment_" in seg["name"] for seg in segments)


def test_bpm_match_score(mock_spotify_service):
    """Test BPM match score calculation."""
    generator = PlaylistGenerator(mock_spotify_service)

    # Perfect match
    assert generator._bpm_match_score(140, [130, 150]) == 1.0

    # Within range
    assert generator._bpm_match_score(135, [130, 150]) == 1.0

    # Out of range (penalty)
    score = generator._bpm_match_score(120, [130, 150])
    assert 0 < score < 1.0


def test_calculate_affinity(mock_spotify_service):
    """Test user affinity calculation."""
    from app.models.playlist import Track

    generator = PlaylistGenerator(mock_spotify_service)

    track = Track(
        id="test",
        name="Test",
        artist="Test Artist",
        artist_id="artist_1",
        duration_ms=200000,
        spotify_url="https://test.com",
        spotify_uri="spotify:track:test",
        tempo=140.0,
        bpm=140.0,
        energy=0.8,
        danceability=0.7,
        valence=0.6,
        genres=["pop"],
    )

    user_prefs = {
        "top_genres": ["pop"],
        "top_artists": ["artist_1"],
    }

    affinity = generator._calculate_affinity(track, user_prefs)
    assert affinity > 0.5  # Should be higher due to matches


async def test_generate_with_excluded_tracks(
    mock_spotify_service, workout_steady, user_preferences, mock_spotify_track
):
    """Test playlist generation with excluded track IDs."""
    # Setup mocks
    excluded_track_id = "excluded_track_id"
    mock_spotify_service.get_recommendations = AsyncMock(
        return_value=[mock_spotify_track] * 10
    )

    generator = PlaylistGenerator(mock_spotify_service)

    # Generate with excluded tracks
    result = await generator.generate(
        workout_steady,
        user_preferences,
        excluded_track_ids=[excluded_track_id]
    )

    assert result.total_tracks > 0
    # Verify excluded track is not in result
    excluded_ids = [track.id for track in result.tracks]
    assert excluded_track_id not in excluded_ids


async def test_generate_playlist_duration_validation(
    mock_spotify_service, workout_steady, user_preferences, mock_spotify_track
):
    """Test that generated playlist duration is longer than workout duration."""
    # Setup mocks - return enough tracks to meet duration requirement
    mock_spotify_service.get_recommendations = AsyncMock(
        return_value=[mock_spotify_track] * 50  # More tracks for better selection
    )

    generator = PlaylistGenerator(mock_spotify_service)

    result = await generator.generate(workout_steady, user_preferences)

    workout_duration_seconds = workout_steady.duration_minutes * 60
    assert result.total_duration >= workout_duration_seconds
    assert len(result.tracks) > 0
