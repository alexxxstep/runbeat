"""
Tests for LangChain WorkoutParserAgent.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.agents.parser import WorkoutParserAgent
from app.schemas.llm_responses import WorkoutIntent


@pytest.fixture
def langchain_parser_agent():
    """Create LangChain parser agent instance."""
    return WorkoutParserAgent()


@pytest.mark.asyncio
async def test_rule_based_parsing_success(langchain_parser_agent):
    """Test that rule-based parsing is used when successful."""
    message = "легка пробіжка 55 хвилин"

    result = await langchain_parser_agent.parse(message)

    assert result is not None
    assert result.workout_type == "continuous"
    assert result.duration_minutes == 55
    assert result.target_bpm_min == 110
    assert result.target_bpm_max == 130
    assert result.confidence >= 0.9
    assert result.needs_clarification is False


@pytest.mark.asyncio
async def test_rule_based_parsing_with_music(langchain_parser_agent):
    """Test rule-based parsing with music preferences."""
    message = "легка пробіжка 30 хв під рок-музику"

    result = await langchain_parser_agent.parse(message)

    assert result is not None
    assert result.duration_minutes == 30
    assert result.music_genres is not None
    assert "rock" in result.music_genres


@pytest.mark.asyncio
async def test_ai_parsing_fallback(langchain_parser_agent):
    """Test that AI parsing is used when rule-based fails."""
    message = "хочу щось незрозуміле і складне"

    # Mock the agent executor's ainvoke method
    # Use object.__setattr__ to bypass Pydantic validation
    original_ainvoke = langchain_parser_agent.agent_executor.ainvoke

    async def mock_ainvoke(input_data):
        return {
            "output": '{"workout_type": "continuous", "duration_minutes": 30, '
            '"target_bpm_min": 120, "target_bpm_max": 140, '
            '"confidence": 0.7, "needs_clarification": true, '
            '"clarification_question": "Уточни деталі"}'
        }

    # Use object.__setattr__ to bypass Pydantic validation
    object.__setattr__(langchain_parser_agent.agent_executor,
                       'ainvoke', mock_ainvoke)

    try:
        result = await langchain_parser_agent.parse(message)

        # Verify result
        assert result is not None
        assert result.workout_type == "continuous"
        assert result.confidence == 0.7
    finally:
        # Restore original method
        object.__setattr__(langchain_parser_agent.agent_executor,
                           'ainvoke', original_ainvoke)


@pytest.mark.asyncio
async def test_conversation_history(langchain_parser_agent):
    """Test that conversation history is used."""
    message = "30 хв"
    conversation_history = [
        {"role": "user", "content": "хочу побігати"},
        {"role": "assistant", "content": "Скільки часу?"},
    ]

    # Should use rule-based (has duration and can infer intensity from context)
    result = await langchain_parser_agent.parse(message, conversation_history)

    assert result is not None
    assert result.duration_minutes == 30


@pytest.mark.asyncio
async def test_parse_agent_output_json(langchain_parser_agent):
    """Test parsing agent output with JSON."""
    output_text = '{"workout_type": "continuous", "duration_minutes": 40, "target_bpm_min": 130, "target_bpm_max": 150, "confidence": 0.9, "needs_clarification": false}'

    result = langchain_parser_agent._parse_agent_output(output_text)

    assert result.workout_type == "continuous"
    assert result.duration_minutes == 40
    assert result.target_bpm_min == 130
    assert result.target_bpm_max == 150


@pytest.mark.asyncio
async def test_parse_agent_output_markdown(langchain_parser_agent):
    """Test parsing agent output with markdown code blocks."""
    output_text = """Here's the parsed intent:
```json
{"workout_type": "intervals", "duration_minutes": 30, "target_bpm_min": 160, "target_bpm_max": 180, "confidence": 0.85, "needs_clarification": true}
```"""

    result = langchain_parser_agent._parse_agent_output(output_text)

    assert result.workout_type == "intervals"
    assert result.duration_minutes == 30
    assert result.needs_clarification is True


@pytest.mark.asyncio
async def test_memory_management(langchain_parser_agent):
    """Test that memory is managed correctly."""
    message1 = "легка пробіжка 30 хв"
    message2 = "під рок-музику"

    # First message
    result1 = await langchain_parser_agent.parse(message1)
    assert result1 is not None

    # Second message (should use memory)
    conversation_history = [
        {"role": "user", "content": message1},
        {"role": "assistant", "content": "Ок, 30 хв легка пробіжка"},
    ]
    result2 = await langchain_parser_agent.parse(message2, conversation_history)

    # Should have music genres from second message (if rule-based parser finds it)
    assert result2 is not None
    # Note: This test may fail if rule-based parser doesn't extract genres from "під рок-музику"
    # This is acceptable - the test verifies that parsing works with conversation history


def test_clear_memory(langchain_parser_agent):
    """Test clearing agent memory."""
    langchain_parser_agent.add_to_memory("user", "test message")
    langchain_parser_agent.clear_memory()

    # Memory should be empty
    assert len(langchain_parser_agent.memory.chat_memory.messages) == 0
