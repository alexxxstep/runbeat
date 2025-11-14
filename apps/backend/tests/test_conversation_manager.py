"""
Tests for conversation manager.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.services.conversation_manager import (
    ConversationManager,
    ConversationStateEnum,
    ConversationAction,
)
from app.schemas.llm_responses import WorkoutIntent, IntervalPhase, PlaylistResponse, PlaylistTrack


@pytest.fixture
def llm_service_mock():
    """Mock LLM service."""
    service = Mock()
    service.parse_workout = AsyncMock()
    service.generate_playlist = AsyncMock()
    return service


@pytest.fixture
def conversation_manager(llm_service_mock):
    """Create conversation manager with mocked LLM service."""
    # Mock SpotifyService to avoid actual Spotify API calls
    from unittest.mock import MagicMock
    spotify_service_mock = MagicMock()
    manager = ConversationManager(
        llm_service=llm_service_mock,
        spotify_service=spotify_service_mock
    )
    # Mock _save_conversation to avoid database calls in tests
    manager._save_conversation = AsyncMock()
    return manager


@pytest.mark.asyncio
async def test_new_conversation_creation(conversation_manager, llm_service_mock):
    """Test creating new conversation."""
    user_id = "test-user-123"
    message = "Хочу пробігти 30 хв"

    # Mock complete workout intent
    mock_intent = WorkoutIntent(
        workout_type="continuous",
        duration_minutes=30,
        target_bpm_min=120,
        target_bpm_max=135,
        energy_profile="steady",
        confidence=0.95,
        needs_clarification=False,
    )

    llm_service_mock.parse_workout.return_value = mock_intent

    # Mock playlist generation
    mock_playlist = PlaylistResponse(
        playlist_name="Test Playlist",
        total_tracks=10,
        total_duration_minutes=30.0,
        bpm_range=[120, 135],
        progression_type="steady",
        primary_genres=["pop"],
        tracks=[],
        curation_notes="Test notes",
    )
    llm_service_mock.generate_playlist.return_value = mock_playlist

    conversation_id, response = await conversation_manager.process_message(
        user_id=user_id, message=message
    )

    assert conversation_id is not None
    assert conversation_id in conversation_manager.conversations
    assert response["state"] == ConversationStateEnum.COMPLETE
    assert response["action"] == ConversationAction.SHOW_PLAYLIST


@pytest.mark.asyncio
async def test_clarification_needed(conversation_manager, llm_service_mock):
    """Test conversation asks for clarification."""
    user_id = "test-user-123"
    message = "хочу побігати"

    # Mock intent that needs clarification
    mock_intent = WorkoutIntent(
        workout_type="continuous",
        duration_minutes=30,  # Default guess
        target_bpm_min=120,
        target_bpm_max=135,
        energy_profile="steady",
        confidence=0.4,  # Low confidence!
        needs_clarification=True,
        clarification_question="Скільки часу плануєш бігти?",
    )

    llm_service_mock.parse_workout.return_value = mock_intent

    conversation_id, response = await conversation_manager.process_message(
        user_id=user_id, message=message
    )

    assert response["state"] == ConversationStateEnum.NEEDS_CLARIFICATION
    assert response["action"] == ConversationAction.ASK_CLARIFICATION
    assert "Скільки часу" in response["message_to_user"]


@pytest.mark.asyncio
async def test_multi_turn_conversation(conversation_manager, llm_service_mock):
    """Test multi-turn conversation flow."""
    user_id = "test-user-123"

    # Turn 1: Vague request
    mock_intent_1 = WorkoutIntent(
        workout_type="intervals",
        duration_minutes=40,
        target_bpm_min=130,
        target_bpm_max=170,
        intervals=None,  # Missing!
        energy_profile="wave",
        confidence=0.6,
        needs_clarification=True,
        clarification_question="Який інтервал роботи/відпочинку?",
    )
    llm_service_mock.parse_workout.return_value = mock_intent_1

    conv_id, response1 = await conversation_manager.process_message(
        user_id=user_id, message="Хочу інтервали 40 хв"
    )

    assert response1["state"] == ConversationStateEnum.NEEDS_CLARIFICATION

    # Turn 2: Provide interval pattern
    mock_intent_2 = WorkoutIntent(
        workout_type="intervals",
        duration_minutes=40,
        target_bpm_min=130,
        target_bpm_max=170,
        intervals=[
            IntervalPhase(type="work", duration_minutes=5, target_bpm=170),
            IntervalPhase(type="rest", duration_minutes=2, target_bpm=130),
        ],
        energy_profile="wave",
        confidence=0.95,
        needs_clarification=False,
    )
    llm_service_mock.parse_workout.return_value = mock_intent_2

    # Mock playlist
    mock_playlist = PlaylistResponse(
        playlist_name="Interval Playlist",
        total_tracks=12,
        total_duration_minutes=40.0,
        bpm_range=[130, 170],
        progression_type="wave",
        primary_genres=["electronic"],
        tracks=[],
        curation_notes="Interval workout playlist",
    )
    llm_service_mock.generate_playlist.return_value = mock_playlist

    conv_id, response2 = await conversation_manager.process_message(
        user_id=user_id, message="5-2", conversation_id=conv_id
    )

    assert response2["state"] == ConversationStateEnum.COMPLETE
    assert response2["playlist"] is not None


def test_is_intent_complete(conversation_manager):
    """Test intent completeness check."""
    # Complete intent
    complete_intent = WorkoutIntent(
        workout_type="continuous",
        duration_minutes=30,
        target_bpm_min=145,
        target_bpm_max=160,
        energy_profile="steady",
        confidence=0.95,
    )

    assert conversation_manager._is_intent_complete(complete_intent)

    # Incomplete: Low confidence
    low_confidence = WorkoutIntent(
        workout_type="continuous",
        duration_minutes=30,
        target_bpm_min=145,
        target_bpm_max=160,
        energy_profile="steady",
        confidence=0.5,  # Too low!
    )

    assert not conversation_manager._is_intent_complete(low_confidence)

    # Incomplete: Missing intervals
    missing_intervals = WorkoutIntent(
        workout_type="intervals",
        duration_minutes=40,
        target_bpm_min=130,
        target_bpm_max=170,
        intervals=None,  # Missing!
        energy_profile="wave",
        confidence=0.95,
    )

    assert not conversation_manager._is_intent_complete(missing_intervals)

    # Incomplete: Missing duration (use model_construct to bypass validation for test)
    missing_duration = WorkoutIntent.model_construct(
        workout_type="continuous",
        duration_minutes=4,  # Below minimum of 5
        target_bpm_min=145,
        target_bpm_max=160,
        energy_profile="steady",
        confidence=0.95,
    )

    assert not conversation_manager._is_intent_complete(missing_duration)


def test_generate_follow_up_question(conversation_manager):
    """Test follow-up question generation."""
    # Missing duration (use model_construct to bypass validation for test)
    intent = WorkoutIntent.model_construct(
        workout_type="continuous",
        duration_minutes=4,  # Below minimum of 5
        target_bpm_min=120,
        target_bpm_max=135,
        energy_profile="steady",
        confidence=0.7,
    )

    conversation = {"messages": []}
    question = conversation_manager._generate_follow_up_question(intent, conversation)
    assert "скільки часу" in question.lower()

    # Low confidence
    low_conf = WorkoutIntent(
        workout_type="continuous",
        duration_minutes=30,
        target_bpm_min=120,
        target_bpm_max=135,
        energy_profile="steady",
        confidence=0.5,
    )

    conversation = {"messages": []}
    question = conversation_manager._generate_follow_up_question(low_conf, conversation)
    assert "інтенсивність" in question.lower()

    # Missing intervals
    missing_intervals = WorkoutIntent(
        workout_type="intervals",
        duration_minutes=40,
        target_bpm_min=130,
        target_bpm_max=170,
        intervals=None,
        energy_profile="wave",
        confidence=0.8,
    )

    conversation = {"messages": []}
    question = conversation_manager._generate_follow_up_question(
        missing_intervals, conversation
    )
    assert "інтервал" in question.lower()


def test_get_conversation(conversation_manager):
    """Test getting conversation by ID."""
    user_id = "test-user-123"
    conv_id = conversation_manager._create_conversation(user_id)

    conversation = conversation_manager.get_conversation(conv_id)
    assert conversation is not None
    assert conversation["user_id"] == user_id
    assert conversation["state"] == ConversationStateEnum.NEW

    # Non-existent conversation
    assert conversation_manager.get_conversation("non-existent") is None


def test_clear_old_conversations(conversation_manager):
    """Test clearing old conversations."""
    user_id = "test-user-123"
    conv_id = conversation_manager._create_conversation(user_id)

    # Conversation should exist
    assert conv_id in conversation_manager.conversations

    # Clear old conversations (with very short max_age)
    conversation_manager.clear_old_conversations(max_age_hours=0)

    # Conversation should be cleared
    assert conv_id not in conversation_manager.conversations


def test_format_playlist_message(conversation_manager):
    """Test playlist message formatting."""
    playlist = PlaylistResponse(
        playlist_name="Test Playlist",
        total_tracks=10,
        total_duration_minutes=30.5,
        bpm_range=[120, 135],
        progression_type="steady",
        primary_genres=["pop"],
        tracks=[],
        curation_notes="Test notes",
    )

    message = conversation_manager._format_playlist_message(playlist)
    assert "10 треків" in message
    assert "30.5" in message
    assert "120-135 BPM" in message
    assert "Test notes" in message

