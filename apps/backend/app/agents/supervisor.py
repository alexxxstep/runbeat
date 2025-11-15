"""
Supervisor (Conversation Orchestrator) using LangChain.
"""
from typing import Dict

from loguru import logger

from app.schemas.conversation import ConversationState
from app.services.workout_builder import WorkoutBuilder


class SupervisorAgent:
    """
    The main agent that orchestrates the conversation flow.
    It manages the conversation state and delegates tasks to specialized agents.
    """  # noqa: E501

    def __init__(self):
        self.builder_service = WorkoutBuilder()
        self.states: Dict[str, ConversationState] = {}
        logger.info("SupervisorAgent initialized with Builder.")

    def _get_or_create_state(self, user_id: str) -> ConversationState:
        """Retrieves or creates a conversation state for a user."""
        if not user_id or not isinstance(user_id, str) or not user_id.strip():
            raise ValueError("user_id must be a non-empty string")

        if user_id not in self.states:
            logger.info(
                f"Creating new conversation state for user_id: {user_id}")
            self.states[user_id] = ConversationState(user_id=user_id)
        return self.states[user_id]

    async def handle_message(self, user_id: str, message: str) -> str:
        """
        Main entry point for handling a user's message.
        All conversation logic is handled by the WorkoutBuilder AI agent
        via prompts.
        """
        state = self._get_or_create_state(user_id)

        # Delegate the conversation to the WorkoutBuilder AI agent
        # The agent handles all logic including workout creation via its prompt
        update = await self.builder_service.process_message(state, message)

        # Update the state with the new state from the builder agent
        self.states[user_id] = update.new_state

        response_message = update.response_message

        # Check if workout was successfully created
        # (agent indicates this in response)
        # The agent uses create_workout_from_params tool and responds
        success_indicators = (
            "✅" in response_message
            and ("створено" in response_message.lower()
                 or "created" in response_message.lower())
        )
        # Log state before potential clearing
        if user_id in self.states:
            logger.debug(
                f"State for user {user_id}: "
                f"{self.states[user_id].model_dump_json(indent=2)}"
            )

        if success_indicators:
            # Check if response contains error before clearing state
            if "error" not in response_message.lower():
                # Workout was successfully created by the agent - clear state
                logger.info(
                    f"Workout created successfully for user {user_id}, "
                    f"clearing state"
                )
                self.clear_state(user_id)
            else:
                logger.warning(
                    f"Workout creation reported success but contains error "
                    f"for user {user_id}, keeping state"
                )
        elif any(word in response_message.lower()
                 for word in ["скасовано", "canceled", "cancelled"]):
            # User declined - clear state
            logger.info(
                f"Workout creation declined by user {user_id}, "
                f"clearing state"
            )
            self.clear_state(user_id)

        return response_message

    def clear_state(self, user_id: str):
        """Clears the conversation state for a user."""
        if user_id in self.states:
            del self.states[user_id]
            logger.info(f"Cleared conversation state for user_id: {user_id}")


supervisor_agent = SupervisorAgent()
