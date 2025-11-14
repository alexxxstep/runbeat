"""
Tests for workout parser agent.
"""
import pytest
from unittest.mock import Mock, AsyncMock
from app.services.workout_parser_agent import WorkoutParserAgent
from app.services.llm_service import LLMService
from app.schemas.llm_responses import WorkoutIntent


@pytest.fixture
def llm_service_mock():
    """Mock LLM service."""
    service = Mock(spec=LLMService)
    service.parse_workout = AsyncMock()
    return service


@pytest.fixture
def parser_agent(llm_service_mock):
    """Create parser agent with mocked LLM service."""
    return WorkoutParserAgent(llm_service=llm_service_mock)


@pytest.mark.asyncio
async def test_rule_based_parsing_success(parser_agent):
    """Test that rule-based parsing is used when successful."""
    message = "легка пробіжка 55 хвилин"

    # Rule-based parser should handle this
    result = await parser_agent.parse(message)

    # Should not call AI if rule-based succeeds
    parser_agent.llm_service.parse_workout.assert_not_called()

    # Verify result
    assert result is not None
    assert result.duration_minutes == 55
    assert result.confidence >= 0.9


@pytest.mark.asyncio
async def test_ai_parsing_fallback(parser_agent, llm_service_mock):
    """Test that AI parsing is used when rule-based fails."""
    message = "хочу щось незрозуміле"

    # Mock AI response
    mock_ai_intent = WorkoutIntent(
        workout_type="continuous",
        duration_minutes=30,
        target_bpm_min=120,
        target_bpm_max=140,
        confidence=0.7,
        needs_clarification=True,
        clarification_question="Уточни деталі",
    )
    llm_service_mock.parse_workout.return_value = mock_ai_intent

    result = await parser_agent.parse(message)

    # Should call AI
    llm_service_mock.parse_workout.assert_called_once()

    # Verify result
    assert result is not None
    assert result == mock_ai_intent


@pytest.mark.asyncio
async def test_merge_results(parser_agent, llm_service_mock):
    """Test merging rule-based and AI results."""
    message = "легка пробіжка"  # Has intensity but no duration

    # Mock AI response with duration
    mock_ai_intent = WorkoutIntent(
        workout_type="continuous",
        duration_minutes=30,
        target_bpm_min=120,
        target_bpm_max=140,
        confidence=0.8,
        needs_clarification=False,
    )
    llm_service_mock.parse_workout.return_value = mock_ai_intent

    result = await parser_agent.parse(message)

    # Should call AI (rule-based found partial info)
    llm_service_mock.parse_workout.assert_called_once()

    # Result should be merged
    assert result is not None
    # Rule-based found intensity (110-130), AI found duration (30)
    assert result.duration_minutes == 30
    # Should use rule-based BPM if it's more specific
    assert result.target_bpm_min in [110, 120]  # Either rule-based or AI


@pytest.mark.asyncio
async def test_conversation_history_passed(parser_agent, llm_service_mock):
    """Test that conversation history is passed to AI parser."""
    message = "щось складне"
    conversation_history = [
        {"role": "user", "content": "привіт"},
        {"role": "assistant", "content": "Привіт! Як можу допомогти?"},
    ]

    mock_ai_intent = WorkoutIntent(
        workout_type="continuous",
        duration_minutes=30,
        target_bpm_min=120,
        target_bpm_max=140,
        confidence=0.8,
        needs_clarification=False,
    )
    llm_service_mock.parse_workout.return_value = mock_ai_intent

    await parser_agent.parse(
        message=message,
        conversation_history=conversation_history,
    )

    # Verify conversation history was passed
    call_args = llm_service_mock.parse_workout.call_args
    assert call_args is not None
    # Check that conversation_state was passed (it's built from history)
    assert "conversation_state" in call_args.kwargs or len(call_args.args) > 1

