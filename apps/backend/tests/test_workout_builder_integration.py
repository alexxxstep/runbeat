"""
Integration tests for WorkoutBuilder with new AI-driven approach.
Tests the full conversation flow with mocked OpenAI responses.
"""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.workout_builder import WorkoutBuilder
from app.schemas.conversation import ConversationState


@pytest.fixture
def workout_builder():
    """Create WorkoutBuilder instance for testing."""
    return WorkoutBuilder()


@pytest.fixture
def initial_state():
    """Create initial conversation state."""
    return ConversationState(
        user_id="test_user_123",
        collected_parameters={},
        last_question="none",
        history=[]
    )


class TestWorkoutBuilderIntegration:
    """Integration tests for WorkoutBuilder conversation flow."""

    @pytest.mark.asyncio
    async def test_problematic_scenario_fixed(self, workout_builder, initial_state):
        """
        Test the problematic scenario from user's example.
        This should NOT repeat questions anymore.

        Scenario:
        1. User: "інтервальна"
        2. User: "44 хвилин"
        3. User: "класика джаз"
        4. User: "так"
        5. User: "середня"

        Expected: Agent should acknowledge each response and not repeat questions.
        """
        # Mock the agent executor ainvoke method
        with patch('app.services.workout_builder.AgentExecutor.ainvoke', new_callable=AsyncMock) as mock_invoke:

            # Message 1: "інтервальна"
            mock_invoke.return_value = {
                "output": "Чудово! Інтервальна тренування — це дуже ефективно! 🏃‍♂️ Скільки часу плануєш бігти і яка буде інтенсивність?"
            }

            response1 = await workout_builder.process_message(initial_state, "інтервальна")

            assert "інтервальна" in response1.response_message.lower() or "інтервал" in response1.response_message.lower()
            assert "тривалість" in response1.response_message.lower() or "скільки" in response1.response_message.lower()
            # Should NOT repeat the same question
            assert response1.response_message != "Яка планується тривалість та інтенсивність?"

            state = response1.new_state

            # Message 2: "44 хвилин"
            mock_invoke.return_value = {
                "output": "Супер! 44 хвилини інтервалів. Яка буде інтенсивність — середня чи висока?"
            }

            response2 = await workout_builder.process_message(state, "44 хвилин")

            # Should acknowledge the duration
            assert "44" in response2.response_message
            # Should ask for intensity, NOT repeat duration question
            assert "інтенсивність" in response2.response_message.lower()
            assert response2.response_message != "Яка планується тривалість та інтенсивність?"

            state = response2.new_state

            # Message 3: "класика джаз"
            mock_invoke.return_value = {
                "output": "Бачу ти обрав музику (classical і jazz — чудовий вибір! 🎵), але мені ще потрібно знати інтенсивність тренування."
            }

            response3 = await workout_builder.process_message(state, "класика джаз")

            # Should acknowledge the genres
            assert any(word in response3.response_message.lower() for word in ["класик", "джаз", "classical", "jazz", "музик"])
            # Should still ask for intensity (missing parameter)
            assert "інтенсивність" in response3.response_message.lower()

            state = response3.new_state

            # Message 4: "так" (confirmation without all params - should ask for missing)
            mock_invoke.return_value = {
                "output": "Я розумію, що ти готовий, але мені ще потрібно знати інтенсивність тренування. Буде середня чи висока?"
            }

            response4 = await workout_builder.process_message(state, "так")

            # Should ask for missing intensity
            assert "інтенсивність" in response4.response_message.lower()

            state = response4.new_state

            # Message 5: "середня"
            mock_invoke.return_value = {
                "output": "Відмінно! Отже, середня інтервальна тренування на 44 хвилини під classical і jazz. Створюємо воркаут?"
            }

            response5 = await workout_builder.process_message(state, "середня")

            # Should summarize everything and ask for confirmation
            assert "44" in response5.response_message
            assert any(word in response5.response_message.lower() for word in ["середня", "moderate"])
            assert any(word in response5.response_message.lower() for word in ["створ", "create"])

    @pytest.mark.asyncio
    async def test_all_info_at_once(self, workout_builder, initial_state):
        """
        Test when user provides all information at once.
        """
        with patch('app.services.workout_builder.AgentExecutor.ainvoke', new_callable=AsyncMock) as mock_invoke:

            mock_invoke.return_value = {
                "output": "Чудово! Легка пробіжка на 30 хвилин під rock — звучить ідеально! Створюємо воркаут?"
            }

            response = await workout_builder.process_message(
                initial_state,
                "легка пробіжка 30 хвилин під рок"
            )

            # Should recognize all parameters and ask for confirmation
            assert "30" in response.response_message
            assert any(word in response.response_message.lower() for word in ["легка", "low"])
            assert any(word in response.response_message.lower() for word in ["rock", "рок"])
            assert any(word in response.response_message.lower() for word in ["створ", "create"])

    @pytest.mark.asyncio
    async def test_context_building(self, workout_builder, initial_state):
        """
        Test that context is built correctly for the agent.
        """
        # Add some history
        initial_state.history = [
            {"role": "user", "content": "хочу пробігти"},
            {"role": "assistant", "content": "Чудово! Скільки часу плануєш бігти?"}
        ]
        initial_state.collected_parameters = {
            "duration_minutes": 45,
            "intensity": "moderate"
        }

        context = workout_builder._build_conversation_context(initial_state, "електро")

        # Check that context includes all necessary information
        assert "User ID: test_user_123" in context
        assert "Current user message: електро" in context
        assert "Already collected parameters:" in context
        assert "duration_minutes" in context
        assert "45" in context
        assert "moderate" in context
        assert "Conversation history" in context

    @pytest.mark.asyncio
    async def test_fallback_response_missing_duration(self, workout_builder, initial_state):
        """
        Test fallback response when duration is missing.
        """
        initial_state.collected_parameters = {}

        fallback = workout_builder._get_fallback_response(initial_state, "хочу пробігти")

        assert "тривалість" in fallback.lower()
        assert "інтенсивність" in fallback.lower()

    @pytest.mark.asyncio
    async def test_fallback_response_missing_genres(self, workout_builder, initial_state):
        """
        Test fallback response when genres are missing.
        """
        initial_state.collected_parameters = {
            "duration_minutes": 45,
            "intensity": "moderate"
        }

        fallback = workout_builder._get_fallback_response(initial_state, "")

        assert "музик" in fallback.lower()
        assert "жанр" in fallback.lower()

    @pytest.mark.asyncio
    async def test_fallback_response_all_collected(self, workout_builder, initial_state):
        """
        Test fallback response when all parameters are collected.
        """
        initial_state.collected_parameters = {
            "duration_minutes": 45,
            "intensity": "moderate",
            "genres": ["electronic", "rock"]
        }

        fallback = workout_builder._get_fallback_response(initial_state, "")

        assert "45" in fallback
        assert "середня" in fallback
        assert "electronic" in fallback or "rock" in fallback
        assert "створ" in fallback.lower()

    @pytest.mark.asyncio
    async def test_fallback_response_confirmation(self, workout_builder, initial_state):
        """
        Test fallback response when user confirms.
        """
        initial_state.last_question = "final_confirmation"
        initial_state.collected_parameters = {
            "duration_minutes": 45,
            "intensity": "moderate",
            "genres": ["electronic"]
        }

        fallback_yes = workout_builder._get_fallback_response(initial_state, "так")
        assert "створю" in fallback_yes.lower()

        fallback_no = workout_builder._get_fallback_response(initial_state, "ні")
        assert "зрозуміло" in fallback_no.lower()

    def test_determine_question_type_confirmation(self, workout_builder, initial_state):
        """
        Test question type determination for confirmation.
        """
        initial_state.collected_parameters = {
            "duration_minutes": 45,
            "intensity": "moderate",
            "genres": ["electronic"]
        }

        question_type = workout_builder._determine_question_type_from_response(
            "Створюємо воркаут?",
            initial_state
        )

        assert question_type == "final_confirmation"

    def test_determine_question_type_genres(self, workout_builder, initial_state):
        """
        Test question type determination for genres.
        """
        initial_state.collected_parameters = {
            "duration_minutes": 45,
            "intensity": "moderate"
        }

        question_type = workout_builder._determine_question_type_from_response(
            "Яку музику ти хочеш слухати?",
            initial_state
        )

        assert question_type == "genres"

    def test_determine_question_type_goal(self, workout_builder, initial_state):
        """
        Test question type determination for workout goal.
        """
        initial_state.collected_parameters = {}

        question_type = workout_builder._determine_question_type_from_response(
            "Яка планується тривалість та інтенсивність?",
            initial_state
        )

        assert question_type == "goal_clarification"

    @pytest.mark.asyncio
    async def test_error_handling(self, workout_builder, initial_state):
        """
        Test that errors are handled gracefully.
        """
        with patch('app.services.workout_builder.AgentExecutor.ainvoke', new_callable=AsyncMock) as mock_invoke:
            # Simulate an error
            mock_invoke.side_effect = Exception("Test error")

            response = await workout_builder.process_message(initial_state, "тест")

            # Should return error message, not crash
            assert "помилка" in response.response_message.lower() or "вибачте" in response.response_message.lower()
            assert response.new_state is not None

    @pytest.mark.asyncio
    async def test_history_management(self, workout_builder, initial_state):
        """
        Test that conversation history is managed correctly.
        """
        with patch('app.services.workout_builder.AgentExecutor.ainvoke', new_callable=AsyncMock) as mock_invoke:

            mock_invoke.return_value = {"output": "Тестова відповідь"}

            # Send first message
            response1 = await workout_builder.process_message(initial_state, "перше повідомлення")

            # Check history after first message
            assert len(response1.new_state.history) == 2  # user + assistant
            assert response1.new_state.history[0]["role"] == "user"
            assert response1.new_state.history[0]["content"] == "перше повідомлення"
            assert response1.new_state.history[1]["role"] == "assistant"

            # Send second message
            response2 = await workout_builder.process_message(response1.new_state, "друге повідомлення")

            # Check history after second message
            assert len(response2.new_state.history) == 4  # 2 user + 2 assistant
            assert response2.new_state.history[2]["role"] == "user"
            assert response2.new_state.history[2]["content"] == "друге повідомлення"

