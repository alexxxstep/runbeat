"""
Supervisor (Conversation Orchestrator) using LangChain.
"""
from typing import Dict
from loguru import logger

from app.schemas.conversation import ConversationState
from app.schemas.workout import Workout
from app.agents.workout_builder_agent import WorkoutBuilderAgent
from app.agents.manager import WorkoutManagerAgent


class SupervisorAgent:
    """
    The main agent that orchestrates the conversation flow.
    It manages the conversation state and delegates tasks to specialized agents.
    """

    def __init__(self):
        self.builder_agent = WorkoutBuilderAgent()
        self.manager_agent = WorkoutManagerAgent()
        self.states: Dict[str, ConversationState] = {}
        logger.info("SupervisorAgent initialized with Builder and Manager.")

    def _get_or_create_state(self, user_id: str) -> ConversationState:
        """Retrieves or creates a conversation state for a user."""
        if user_id not in self.states:
            logger.info(
                f"Creating new conversation state for user_id: {user_id}")
            self.states[user_id] = ConversationState(user_id=user_id)
        return self.states[user_id]

    async def handle_message(self, user_id: str, message: str) -> str:
        """
        Main entry point for handling a user's message.
        """
        state = self._get_or_create_state(user_id)

        # Delegate the conversation to the WorkoutBuilderAgent
        update = await self.builder_agent.process_message(state, message)

        # Update the state with the new state from the builder agent
        self.states[user_id] = update.new_state

        response_message = update.response_message

        # Check if the workout is ready for final confirmation and user confirmed
        if (
            state.last_question == "final_confirmation"
            and "так" in message.lower()
            and state.collected_parameters
        ):
            try:
                # Create a Workout object from collected parameters
                workout_data = Workout(
                    user_id=user_id,
                    type=state.collected_parameters.get("type", "steady"),
                    duration_minutes=state.collected_parameters.get(
                        "duration_minutes", 30),
                    intensity=state.collected_parameters.get(
                        "intensity", "moderate"),
                    hr_zones=[120, 150],  # Default HR zones for now
                    genres=state.collected_parameters.get("genres", []),
                    prompt=state.collected_parameters.get("prompt", None),
                )
                created_workout = await self.manager_agent.create_workout(workout_data)
                response_message = f"✅ Воркаут '{created_workout.type}' успішно створено! Тривалість: {created_workout.duration_minutes} хв. Тепер ви можете згенерувати плейлист."
                # Clear state after successful creation
                self.clear_state(user_id)
            except Exception as e:
                logger.error(f"Failed to create workout: {e}")
                response_message = "Виникла помилка при збереженні воркауту. Спробуйте ще раз."
        elif state.last_question == "final_confirmation" and "ні" in message.lower():
            response_message = "Створення воркауту скасовано. Чим ще можу допомогти?"
            self.clear_state(user_id)  # Clear state if user declines

        logger.debug(
            f"New state for user {user_id}: {self.states[user_id].model_dump_json(indent=2)}")

        return response_message

    def clear_state(self, user_id: str):
        """Clears the conversation state for a user."""
        if user_id in self.states:
            del self.states[user_id]
            logger.info(f"Cleared conversation state for user_id: {user_id}")


supervisor_agent = SupervisorAgent()
