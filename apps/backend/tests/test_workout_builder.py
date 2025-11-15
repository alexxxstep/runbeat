"""
Tests for WorkoutBuilder AI agent.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.conversation import ConversationState
from app.services.workout_builder import WorkoutBuilder


@pytest.fixture
def workout_builder():
    """Create WorkoutBuilder instance with mocked LLM."""
    with patch('app.agents.base.ChatOpenAI') as mock_llm_class:
        # Mock LLM response
        mock_llm_instance = MagicMock()
        mock_llm_class.return_value = mock_llm_instance

        builder = WorkoutBuilder()
        return builder


@pytest.fixture
def initial_state():
    """Create initial conversation state."""
    return ConversationState(user_id="test_user_123")


@pytest.mark.asyncio
async def test_initial_greeting(workout_builder, initial_state):
    """Test that agent greets user on first message."""
    mock_ainvoke = AsyncMock(
        return_value={
            "output": (
                "Привіт! Я допоможу тобі створити ідеальне тренування. "
                "Яку пробіжку ти хочеш зробити?"
            )
        }
    )
    object.__setattr__(
        workout_builder.agent_executor, 'ainvoke', mock_ainvoke
    )

    update = await workout_builder.process_message(initial_state, "привіт")

    assert update.response_message is not None
    assert len(update.response_message) > 0
    assert (
        "привіт" in update.response_message.lower()
        or "тренування" in update.response_message.lower()
    )
    # User message + assistant response
    assert len(update.new_state.history) == 2


@pytest.mark.asyncio
async def test_workout_parameter_extraction(
    workout_builder, initial_state
):
    """Test that agent extracts workout parameters from user message."""
    mock_ainvoke = AsyncMock(
        return_value={
            "output": (
                "Чудово! Інтенсивна пробіжка на 48 хвилин - "
                "звучить як виклик! Яку музику ти хочеш слухати?"
            )
        }
    )
    object.__setattr__(
        workout_builder.agent_executor, 'ainvoke', mock_ainvoke
    )

    state = initial_state
    update = await workout_builder.process_message(
        state, "інтенсивна пробіжка на 48 хвилин"
    )

    # Check that parameters were extracted
    assert "duration_minutes" in update.new_state.collected_parameters
    assert update.new_state.collected_parameters["duration_minutes"] == 48
    assert update.new_state.collected_parameters["intensity"] == "high"
    assert update.response_message is not None


@pytest.mark.asyncio
async def test_no_loop_on_same_question(workout_builder, initial_state):
    """Test that agent doesn't ask the same question twice."""
    state = initial_state

    # First message - user provides workout info
    mock_ainvoke1 = AsyncMock(
        return_value={
            "output": (
                "Чудово! Інтенсивна пробіжка на 48 хвилин. "
                "Яку музику ти хочеш слухати?"
            )
        }
    )
    object.__setattr__(
        workout_builder.agent_executor, 'ainvoke', mock_ainvoke1
    )

    update1 = await workout_builder.process_message(
        state, "інтенсивна пробіжка на 48 хвилин"
    )
    state = update1.new_state

    # Second message - user provides music
    mock_ainvoke2 = AsyncMock(
        return_value={
            "output": (
                "Супер! Отже, інтенсивна пробіжка на 48 хвилин під рок. "
                "Створюємо воркаут?"
            )
        }
    )
    object.__setattr__(
        workout_builder.agent_executor, 'ainvoke', mock_ainvoke2
    )

    update2 = await workout_builder.process_message(state, "рок")

    # Agent should NOT ask about music again, should move to confirmation
    assert (
        "музик" not in update2.response_message.lower()
        or "створ" in update2.response_message.lower()
    )
    assert "рок" in update2.response_message.lower()


@pytest.mark.asyncio
async def test_bilingual_support_ukrainian(
    workout_builder, initial_state
):
    """Test that agent responds in Ukrainian when user writes in Ukrainian."""
    mock_ainvoke = AsyncMock(
        return_value={
            "output": (
                "Чудово! Легка пробіжка на 30 хвилин. "
                "Яку музику ти хочеш слухати?"
            )
        }
    )
    object.__setattr__(
        workout_builder.agent_executor, 'ainvoke', mock_ainvoke
    )

    update = await workout_builder.process_message(
        initial_state, "легка пробіжка 30 хвилин"
    )

    # Response should be in Ukrainian
    assert update.response_message is not None
    # Check for Ukrainian characters or words
    assert (
        any(char in update.response_message for char in "іїєґ")
        or "музик" in update.response_message.lower()
    )


@pytest.mark.asyncio
async def test_bilingual_support_english(workout_builder, initial_state):
    """Test that agent responds in English when user writes in English."""
    mock_ainvoke = AsyncMock(
        return_value={
            "output": (
                "Great! Easy 30-minute run. "
                "What music would you like to listen to?"
            )
        }
    )
    object.__setattr__(
        workout_builder.agent_executor, 'ainvoke', mock_ainvoke
    )

    update = await workout_builder.process_message(
        initial_state, "easy run 30 minutes"
    )

    # Response should be in English
    assert update.response_message is not None
    assert (
        "music" in update.response_message.lower()
        or "workout" in update.response_message.lower()
    )


@pytest.mark.asyncio
async def test_complete_workout_info_in_one_message(
    workout_builder, initial_state
):
    """Test that agent handles complete workout info in one message."""
    mock_ainvoke = AsyncMock(
        return_value={
            "output": (
                "Супер! Отже, легка пробіжка на 30 хвилин під рок. "
                "Створюємо воркаут?"
            )
        }
    )
    object.__setattr__(
        workout_builder.agent_executor, 'ainvoke', mock_ainvoke
    )

    update = await workout_builder.process_message(
        initial_state, "хочу легку пробіжку 30 хвилин під рок"
    )

    # Should extract all parameters
    assert update.new_state.collected_parameters.get("duration_minutes") == 30
    assert update.new_state.collected_parameters.get("intensity") == "low"
    assert "рок" in str(
        update.new_state.collected_parameters.get("genres", [])
    )

    # Should ask for confirmation, not ask for more info
    assert (
        "створ" in update.response_message.lower()
        or "confirm" in update.response_message.lower()
    )


@pytest.mark.asyncio
async def test_context_memory(workout_builder, initial_state):
    """Test that agent remembers previous conversation context."""
    state = initial_state

    # First exchange
    mock_ainvoke1 = AsyncMock(
        return_value={
            "output": (
                "Чудово! Інтенсивна пробіжка на 48 хвилин. "
                "Яку музику ти хочеш слухати?"
            )
        }
    )
    object.__setattr__(
        workout_builder.agent_executor, 'ainvoke', mock_ainvoke1
    )
    update1 = await workout_builder.process_message(
        state, "інтенсивна пробіжка на 48 хвилин"
    )
    state = update1.new_state

    # Second exchange - agent should remember duration and intensity
    mock_ainvoke2 = AsyncMock(
        return_value={
            "output": (
                "Супер! Отже, інтенсивна пробіжка на 48 хвилин під рок. "
                "Створюємо воркаут?"
            )
        }
    )
    object.__setattr__(
        workout_builder.agent_executor, 'ainvoke', mock_ainvoke2
    )
    update2 = await workout_builder.process_message(state, "рок")

    # Agent should remember 48 minutes and high intensity
    assert (
        "48" in update2.response_message
        or update2.new_state.collected_parameters.get("duration_minutes")
        == 48
    )


@pytest.mark.asyncio
async def test_error_handling(workout_builder, initial_state):
    """Test that agent handles errors gracefully."""
    mock_ainvoke = AsyncMock(side_effect=Exception("API Error"))
    object.__setattr__(
        workout_builder.agent_executor, 'ainvoke', mock_ainvoke
    )

    update = await workout_builder.process_message(initial_state, "тест")

    # Should return fallback message
    assert update.response_message is not None
    assert (
        "помилк" in update.response_message.lower()
        or "error" in update.response_message.lower()
    )


@pytest.mark.asyncio
async def test_question_type_determination(
    workout_builder, initial_state
):
    """Test that agent correctly determines question type."""
    state = initial_state

    # Test goal clarification
    mock_ainvoke1 = AsyncMock(
        return_value={
            "output": (
                "Чудово! Яка планується тривалість та "
                "інтенсивність тренування?"
            )
        }
    )
    object.__setattr__(
        workout_builder.agent_executor, 'ainvoke', mock_ainvoke1
    )
    update = await workout_builder.process_message(state, "хочу побігати")
    assert update.new_state.last_question == "goal_clarification"

    # Test genres question
    state.collected_parameters = {
        "duration_minutes": 30,
        "intensity": "low",
        "type": "steady",
    }
    mock_ainvoke2 = AsyncMock(
        return_value={
            "output": "Добре! А яку музику ви б хотіли слухати?"
        }
    )
    object.__setattr__(
        workout_builder.agent_executor, 'ainvoke', mock_ainvoke2
    )
    update = await workout_builder.process_message(state, "добре")
    assert update.new_state.last_question == "genres"

    # Test final confirmation
    state.collected_parameters = {
        "duration_minutes": 30,
        "intensity": "low",
        "type": "steady",
        "genres": ["rock"],
    }
    mock_ainvoke3 = AsyncMock(
        return_value={"output": "Супер! Створюємо воркаут?"}
    )
    object.__setattr__(
        workout_builder.agent_executor, 'ainvoke', mock_ainvoke3
    )
    update = await workout_builder.process_message(state, "так")
    assert update.new_state.last_question == "final_confirmation"


@pytest.mark.asyncio
async def test_parameter_extraction_from_user_message(
    workout_builder, initial_state
):
    """Test that parameters are correctly extracted from user messages."""
    test_cases = [
        (
            "легка пробіжка 30 хвилин",
            {"duration_minutes": 30, "intensity": "low"},
        ),
        (
            "інтенсивна пробіжка на 48 хвилин",
            {"duration_minutes": 48, "intensity": "high"},
        ),
        (
            "easy run 30 minutes",
            {"duration_minutes": 30, "intensity": "low"},
        ),
    ]

    for message, expected_params in test_cases:
        mock_ainvoke = AsyncMock(return_value={"output": "Добре!"})
        object.__setattr__(
            workout_builder.agent_executor, 'ainvoke', mock_ainvoke
        )

        update = await workout_builder.process_message(
            initial_state, message
        )

        for key, value in expected_params.items():
            assert update.new_state.collected_parameters.get(key) == value
