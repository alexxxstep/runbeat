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

        # Check if the last step was final confirmation and user confirms
        if state.last_question == "final_confirmation" and "так" in message.lower():
            # Create a Workout object from collected parameters
            workout_to_save = Workout(**state.collected_parameters)

            # Call the manager agent to save the workout
            try:
                result = await self.manager_agent.create_and_activate_workout(
                    user_id=user_id,
                    workout_intent=workout_to_save
                )
                logger.info(
                    f"Workout created for user {user_id}. Result: {result}")

                # Clear state after successful creation
                self.clear_state(user_id)

                return f"✅ Воркаут успішно створено! ID: {result}. Тепер ви можете згенерувати для нього плейлист."

            except Exception as e:
                logger.error(f"Error creating workout for user {user_id}: {e}")
                return "На жаль, сталася помилка при збереженні воркаута. Спробуйте ще раз."

        # Otherwise, continue the conversation with the builder agent
        update = await self.builder_agent.process_message(state, message)
        self.states[user_id] = update.new_state

        logger.debug(
            f"New state for user {user_id}: {update.new_state.model_dump_json(indent=2)}")

        return update.response_message

    def clear_state(self, user_id: str):
        """Clears the conversation state for a user."""
        if user_id in self.states:
            del self.states[user_id]
            logger.info(f"Cleared conversation state for user_id: {user_id}")


supervisor_agent = SupervisorAgent()
