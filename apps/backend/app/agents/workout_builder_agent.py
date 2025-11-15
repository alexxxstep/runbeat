from app.schemas.conversation import ConversationState, ConversationUpdate, CurrentQuestion
from loguru import logger
import re

class WorkoutBuilderAgent:
    """
    An agent that guides the user through creating a workout conversationally.
    """

    async def process_message(
        self, state: ConversationState, user_message: str
    ) -> ConversationUpdate:
        """
        Processes a user's message based on the current conversation state
        and returns the updated state and the next message from the assistant.
        """
        # Add user message to history
        state.history.append({"role": "user", "content": user_message})

        # If conversation is just starting, begin the flow
        if state.last_question == "none":
            return self._start_conversation(state)

        # Process the user's answer to the last question
        state = self._process_answer(state, user_message)

        # Determine the next question to ask
        next_question = self._get_next_question(state)

        # Update the state with the new question
        state.last_question = next_question

        # Generate the assistant's response message
        response_message = self._generate_response(state)

        # Add assistant message to history
        state.history.append({"role": "assistant", "content": response_message})

        return ConversationUpdate(new_state=state, response_message=response_message)

    def _start_conversation(self, state: ConversationState) -> ConversationUpdate:
        state.last_question = "type"
        response_message = "Чудово! Давайте створимо для вас ідеальне тренування. Спочатку оберіть тип тренування: Стабільна, Прогресивна, Інтервальна, або Фартлек?"
        state.history.append({"role": "assistant", "content": response_message})
        return ConversationUpdate(new_state=state, response_message=response_message)

    def _process_answer(self, state: ConversationState, user_message: str) -> ConversationState:
        """Parses the user's message and updates the collected_parameters."""
        last_question = state.last_question

        if last_question == "type":
            # Simple keyword matching for workout type
            if "стабільн" in user_message.lower():
                state.collected_parameters["type"] = "steady"
            elif "прогресивн" in user_message.lower():
                state.collected_parameters["type"] = "progressive"
            elif "інтервальн" in user_message.lower():
                state.collected_parameters["type"] = "intervals"
            elif "фартлек" in user_message.lower():
                state.collected_parameters["type"] = "fartlek"

        elif last_question == "duration":
            # Extract numbers from the message for duration
            numbers = re.findall(r'\d+', user_message)
            if numbers:
                state.collected_parameters["duration_minutes"] = int(numbers[0])

        elif last_question == "intensity":
            if "легк" in user_message.lower():
                state.collected_parameters["intensity"] = "low"
            elif "середн" in user_message.lower():
                state.collected_parameters["intensity"] = "moderate"
            elif "висок" in user_message.lower() or "важк" in user_message.lower():
                state.collected_parameters["intensity"] = "high"

        # TODO: Implement parsing for genres and prompt

        return state

    def _get_next_question(self, state: ConversationState) -> CurrentQuestion:
        """Determines the next logical question based on collected parameters."""
        if "type" not in state.collected_parameters:
            return "type"
        if "duration_minutes" not in state.collected_parameters:
            return "duration"
        if "intensity" not in state.collected_parameters:
            return "intensity"
        if "genres" not in state.collected_parameters:
            return "genres"
        if "prompt" not in state.collected_parameters:
            return "prompt"

        return "final_confirmation"

    def _generate_response(self, state: ConversationState) -> str:
        """Generates the next message for the assistant."""
        next_question = state.last_question

        if next_question == "duration":
            return "Добре, зрозуміло. Яка буде тривалість тренування у хвилинах?"

        if next_question == "intensity":
            return "Прийнято. Тепер оберіть інтенсивність: Легка, Середня, чи Висока?"

        if next_question == "genres":
            # In a real scenario, we would list the genres
            return "Чудово. Які музичні жанри вам подобаються? Можна обрати декілька."

        if next_question == "prompt":
            return "Майже готово. Чи є у вас якісь додаткові побажання до музики? Наприклад, 'енергійна музика для ранку' або 'тільки інструментальні треки'."

        if next_question == "final_confirmation":
            # Build a summary of the workout
            # For now, a simple confirmation
            workout_summary = ", ".join(f"{k}: {v}" for k, v in state.collected_parameters.items())
            return f"Ми зібрали всю інформацію! Ось ваш воркаут: {workout_summary}. Зберегти його?"

        # Fallback message
        return "Вибачте, я не зрозумів. Можете повторити?"
