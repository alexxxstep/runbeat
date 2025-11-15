import pytest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from app.main import app
from app.services.spotify_service import SpotifyService
from app.models.playlist import PlaylistData, Track

client = TestClient(app)

# Helper to create mock tracks
def create_mock_track(track_id: int) -> dict:
    return {
        "id": f"track_{track_id}", "name": f"Track {track_id}", "artist": f"Artist {track_id}",
        "artists": [{"id": f"artist_{track_id}", "name": f"Artist {track_id}"}],
        "artist_id": f"artist_{track_id}", "duration_ms": 200000, "uri": f"spotify:track:track_{track_id}",
        "external_urls": {"spotify": f"https://open.spotify.com/track/track_{track_id}"},
        "tempo": 120.0, "energy": 0.7, "danceability": 0.7, "valence": 0.7, "album": {"name": "Test Album"}
    }

@pytest.fixture
def mock_workout_request():
    """Provides a standard workout request body."""
    return {
        "workout": {"type": "steady", "duration_minutes": 30, "intensity": "moderate", "hr_zones": [130, 150]},
        "user_preferences": {"top_genres": ["pop", "rock"]},
    }

def test_variants_are_generated_successfully(mock_workout_request):
    """
    Tests that two different variants are successfully generated using dependency override.
    """
    mock_service = AsyncMock(spec=SpotifyService)

    async def get_recs_side_effect(*args, **kwargs):
        genres = kwargs.get("seed_genres", [])
        if "pop" in genres:
            return [create_mock_track(i) for i in range(1, 21)]
        else:
            return [create_mock_track(i) for i in range(21, 41)]

    mock_service.get_recommendations.side_effect = get_recs_side_effect

    # Override the dependency
    from app.api.routes.playlists import get_spotify_service
    app.dependency_overrides[get_spotify_service] = lambda: mock_service

    response = client.post("/playlists/preview-variants", json=mock_workout_request)
    assert response.status_code == 200
    data = response.json()

    assert "variant1" in data and "variant2" in data
    assert data['variant1']['total_tracks'] > 0
    assert data['variant2']['total_tracks'] > 0

    variant1_ids = {t['id'] for t in data['variant1']['tracks']}
    variant2_ids = {t['id'] for t in data['variant2']['tracks']}
    assert not variant1_ids.intersection(variant2_ids)

    # Clean up the override
    app.dependency_overrides.clear()


@patch("app.services.playlist_generator.PlaylistGenerator.generate")
def test_fallback_logic_when_alternative_fails(mock_generate, mock_workout_request):
    """
    Tests the fallback logic using dependency override when the alternative variant is empty.
    """
    primary_tracks = [
        Track(
            id=f"track_{i}",
            name=f"Track {i}",
            artist=f"Artist {i}",
            artist_id=f"artist_{i}",
            album="Test",
            duration_ms=200000,
            spotify_url=f"https://open.spotify.com/track/{i}",
            spotify_uri=f"spotify:track:{i}",
            tempo=140.0,
            bpm=140.0,
            energy=0.8,
            danceability=0.7,
            valence=0.6,
            genres=["pop"],
        )
        for i in range(1, 3)
    ]
    playlist_primary = PlaylistData(
        tracks=primary_tracks,
        total_duration=sum(t.duration_ms for t in primary_tracks) / 1000,
        total_tracks=len(primary_tracks),
    )
    playlist_empty = PlaylistData(tracks=[], total_duration=0, total_tracks=0)

    async def generate_side_effect(*args, **kwargs):
        if kwargs.get("variant_strategy") == "primary":
            return playlist_primary
        return playlist_empty

    mock_generate.side_effect = generate_side_effect

    response = client.post("/playlists/preview-variants", json=mock_workout_request)
    assert response.status_code == 200
    data = response.json()

    assert data['variant1']['total_tracks'] > 0
    assert data['variant2']['total_tracks'] == data['variant1']['total_tracks']

    variant1_ids = {t['id'] for t in data['variant1']['tracks']}
    variant2_ids = {t['id'] for t in data['variant2']['tracks']}
    assert variant1_ids == variant2_ids

    app.dependency_overrides.clear()
