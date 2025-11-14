"""
Tests for rule-based parser.
"""
import pytest
from app.services.parsers.rule_based_parser import RuleBasedParser
from app.schemas.llm_responses import WorkoutIntent


@pytest.fixture
def parser():
    """Create rule-based parser instance."""
    return RuleBasedParser()


@pytest.mark.parametrize("message,expected_duration", [
    ("55 хвилин", 55),
    ("30 хв", 30),
    ("1 годину", 60),
    ("півгодини", 30),
    ("легка пробіжка 55 хвилин", 55),
    ("хочу пробігти 40 хв", 40),
])
def test_extract_duration(parser, message, expected_duration):
    """Test duration extraction."""
    result = parser.parse(message)
    if result:
        assert result.duration_minutes == expected_duration


@pytest.mark.parametrize("message,expected_bpm_min,expected_bpm_max", [
    ("легка пробіжка 30 хв", 110, 130),
    ("легкий біг 40 хвилин", 110, 130),
    ("темповий біг 45 хв", 130, 160),
    ("інтервали 30 хв", 160, 180),
    ("швидкий біг 20 хв", 160, 180),
])
def test_extract_intensity(parser, message, expected_bpm_min, expected_bpm_max):
    """Test intensity extraction and BPM mapping."""
    result = parser.parse(message)
    assert result is not None
    assert result.target_bpm_min == expected_bpm_min
    assert result.target_bpm_max == expected_bpm_max


@pytest.mark.parametrize("message,expected_type", [
    ("легка пробіжка 30 хв", "continuous"),
    ("інтервали 30 хв", "intervals"),
    ("фартлек 40 хв", "fartlek"),
    ("відновлення 30 хв", "recovery"),
])
def test_extract_workout_type(parser, message, expected_type):
    """Test workout type extraction."""
    result = parser.parse(message)
    assert result is not None
    assert result.workout_type == expected_type


def test_complete_intent_parsing(parser):
    """Test parsing complete intent."""
    message = "хочу пробігти легку пробіжку 55 хвилин"
    result = parser.parse(message)

    assert result is not None
    assert result.workout_type == "continuous"
    assert result.duration_minutes == 55
    assert result.target_bpm_min == 110
    assert result.target_bpm_max == 130
    assert result.confidence >= 0.9
    assert result.needs_clarification is False


def test_incomplete_intent_returns_none(parser):
    """Test that incomplete intents return None."""
    message = "хочу побігати"  # No duration, no intensity
    result = parser.parse(message)

    assert result is None


def test_music_genres_extraction(parser):
    """Test music genres extraction."""
    message = "легка пробіжка 30 хв під рок-музику"
    result = parser.parse(message)

    assert result is not None
    assert "rock" in (result.music_genres or [])


def test_music_prompt_extraction(parser):
    """Test music prompt extraction."""
    message = "легка пробіжка 30 хв під мотивуючу музику"
    result = parser.parse(message)

    assert result is not None
    assert result.music_prompt is not None
    assert "мотивуюч" in result.music_prompt.lower()


def test_intervals_need_clarification(parser):
    """Test that intervals need clarification for interval pattern."""
    message = "інтервали 30 хв"
    result = parser.parse(message)

    assert result is not None
    assert result.workout_type == "intervals"
    assert result.needs_clarification is True
    assert result.clarification_question is not None


def test_multiple_genres(parser):
    """Test extraction of multiple music genres."""
    message = "легка пробіжка 30 хв під хіп-хоп та електроніку"
    result = parser.parse(message)

    assert result is not None
    assert result.music_genres is not None
    assert "hip-hop" in result.music_genres
    assert "electronic" in result.music_genres

