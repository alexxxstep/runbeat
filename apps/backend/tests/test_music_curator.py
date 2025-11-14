"""
Tests for music curator prompts and playlist generation.
"""
import pytest
from app.services.prompts.prompt_builder import PromptBuilder
from app.services.prompts.music_curator import (
    MUSIC_CURATOR_SYSTEM,
    MUSIC_CURATOR_EXAMPLES,
)
from app.schemas.llm_responses import WorkoutIntent


def test_music_curator_prompt_has_key_sections():
    """Test that music curator prompt has all required sections."""
    prompt = MUSIC_CURATOR_SYSTEM

    # Check key sections exist
    assert "BPM Science" in prompt
    assert "Cadence" in prompt
    assert "Genre Selection" in prompt
    assert "Energy Curve" in prompt
    assert "Warm-up" in prompt
    assert "Cool-down" in prompt
    assert "Playlist Structure" in prompt
    assert "Track Selection" in prompt
    assert "Spotify API Integration" in prompt
    assert "User Preference Learning" in prompt
    assert "Response Format" in prompt
    assert "Quality Checklist" in prompt


def test_music_curator_examples_exist():
    """Test that music curator examples are present."""
    assert MUSIC_CURATOR_EXAMPLES is not None
    assert len(MUSIC_CURATOR_EXAMPLES) > 0
    assert "Example Playlist Generations" in MUSIC_CURATOR_EXAMPLES


def test_build_playlist_prompt_basic():
    """Test basic playlist generation prompt building."""
    builder = PromptBuilder()

    workout_intent = {
        "workout_type": "continuous",
        "duration_minutes": 30,
        "target_bpm_min": 145,
        "target_bpm_max": 160,
        "energy_profile": "steady",
        "confidence": 0.95,
    }

    messages = builder.build_playlist_generation_prompt(
        workout_intent=workout_intent
    )

    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"

    # Check system prompt has music curator content
    system_content = messages[0]["content"]
    assert "music curator" in system_content.lower()
    assert "BPM" in system_content

    # Check user prompt has workout details
    user_content = messages[1]["content"]
    assert "continuous" in user_content or "30" in user_content
    assert "145" in user_content and "160" in user_content


def test_build_playlist_prompt_with_intervals():
    """Test playlist prompt for interval workout."""
    builder = PromptBuilder()

    workout_intent = {
        "workout_type": "intervals",
        "duration_minutes": 40,
        "target_bpm_min": 130,
        "target_bpm_max": 175,
        "intervals": [
            {"type": "work", "duration_minutes": 5, "target_bpm": 170},
            {"type": "rest", "duration_minutes": 2, "target_bpm": 130},
        ],
        "energy_profile": "wave",
        "confidence": 0.9,
    }

    messages = builder.build_playlist_generation_prompt(
        workout_intent=workout_intent
    )

    user_content = messages[1]["content"]
    assert "intervals" in user_content.lower()
    assert "work" in user_content and "rest" in user_content
    assert "5" in user_content and "2" in user_content


def test_build_playlist_prompt_with_user_preferences():
    """Test playlist prompt with user preferences."""
    builder = PromptBuilder()

    workout_intent = {
        "workout_type": "continuous",
        "duration_minutes": 45,
        "target_bpm_min": 120,
        "target_bpm_max": 135,
        "energy_profile": "steady",
        "confidence": 0.95,
    }

    user_preferences = {
        "favorite_genres": ["house", "techno", "indie"],
        "disliked_genres": ["metal"],
        "energy_preference": "high",
        "vocal_preference": "minimal",
    }

    messages = builder.build_playlist_generation_prompt(
        workout_intent=workout_intent,
        user_preferences=user_preferences,
    )

    system_content = messages[0]["content"]
    assert "house" in system_content.lower()
    assert "techno" in system_content.lower()
    assert "metal" in system_content.lower()
    assert "high" in system_content.lower()


def test_analyze_previous_playlists():
    """Test analyzing previous playlists for learning."""
    builder = PromptBuilder()

    previous_playlists = [
        {
            "tracks": [
                {"genre": "house", "skipped": False},
                {"genre": "house", "skipped": False},
                {"genre": "techno", "skipped": True},
                {"genre": "rock", "skipped": True},
                {"genre": "rock", "skipped": True},
            ]
        }
    ]

    stats = builder._analyze_previous_playlists(previous_playlists)

    assert "house" in stats
    assert "techno" in stats
    assert "rock" in stats

    # House: 0% skip rate (0/2)
    assert stats["house"]["skip_rate"] == 0.0

    # Techno: 100% skip rate (1/1)
    assert stats["techno"]["skip_rate"] == 1.0

    # Rock: 100% skip rate (2/2)
    assert stats["rock"]["skip_rate"] == 1.0


def test_analyze_previous_playlists_with_list_genres():
    """Test analyzing playlists where genre is a list."""
    builder = PromptBuilder()

    previous_playlists = [
        {
            "tracks": [
                {"genre": ["house", "electronic"], "skipped": False},
                {"genre": ["techno"], "skipped": True},
            ]
        }
    ]

    stats = builder._analyze_previous_playlists(previous_playlists)

    assert "house" in stats
    assert "techno" in stats


@pytest.mark.asyncio
async def test_llm_service_generate_playlist_mock():
    """Test LLMService playlist generation (mocked)."""
    from unittest.mock import AsyncMock, MagicMock
    from app.services.llm_service import LLMService
    from app.schemas.llm_responses import PlaylistResponse, PlaylistTrack

    service = LLMService()

    workout_intent = WorkoutIntent(
        workout_type="continuous",
        duration_minutes=30,
        target_bpm_min=145,
        target_bpm_max=160,
        energy_profile="steady",
        confidence=0.95,
    )

    # Mock the OpenAI response
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_parsed = PlaylistResponse(
        playlist_name="Test Playlist",
        total_tracks=10,
        total_duration_minutes=30.0,
        bpm_range=[145, 160],
        progression_type="steady",
        primary_genres=["house", "techno"],
        tracks=[
            PlaylistTrack(
                title="Test Track",
                artist="Test Artist",
                bpm=150.0,
                duration_seconds=180.0,
                energy_level=0.8,
                genre="house",
                phase="main",
            )
        ],
        curation_notes="Test notes",
    )
    mock_message.parsed = mock_parsed
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]

    service.client.beta.chat.completions.parse = AsyncMock(
        return_value=mock_response
    )

    playlist = await service.generate_playlist(workout_intent)

    assert playlist is not None
    assert playlist.total_tracks > 0
    assert playlist.total_duration_minutes >= 28  # Allow small variance
    assert playlist.playlist_name == "Test Playlist"

