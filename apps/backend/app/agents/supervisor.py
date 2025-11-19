"""
Supervisor (Conversation Orchestrator) using LangChain.
"""
from typing import Dict

from loguru import logger

from app.schemas.conversation import ConversationState, ConversationUpdate
from app.services.workout_builder import WorkoutBuilder
from app.services.conversation_service import conversation_service


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

    async def handle_message(self, user_id: str, message: str) -> ConversationUpdate:
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
        state = update.new_state
        created_workout = update.created_workout
        needs_clarification = update.needs_clarification
        is_complete = update.is_complete

        # Check if agent created workout (extract from response)
        if "workout_created:" in response_message:
            try:
                import json
                # Extract workout object from agent response
                if "|" in response_message:
                    parts = response_message.split("|", 1)
                    if len(parts) == 2 and parts[0].startswith("workout_created:"):
                        created_workout = json.loads(parts[1])
                        # Clean response message (remove workout data)
                        response_message = "✅ Воркаут успішно створено! Тепер ви можете згенерувати плейлист."
                        is_complete = True
                        needs_clarification = False
            except Exception as e:
                logger.error(f"Failed to parse workout from agent response: {e}")

        # Save conversation to database after each message exchange
        await conversation_service.save_conversation(
            user_id=user_id,
            state=state,
            conversation_state="active"
        )

        # Check if user confirmed workout creation (from fallback or agent)
        message_lower = message.lower().strip()
        is_confirmation = any(
            word in message_lower
            for word in ["так", "yes", "да", "ок", "ok", "створ", "create"]
        )
        is_decline = any(
            word in message_lower
            for word in ["ні", "no", "не треба", "не потрібно", "скасу", "cancel"]
        )

        # If user confirmed and we have all parameters, try to create workout
        if (
            is_confirmation
            and state.last_question == "final_confirmation"
            and state.collected_parameters.get("duration_minutes")
            and state.collected_parameters.get("intensity")
        ):
            # Check if workout was already created by agent
            success_indicators = (
                "✅" in response_message
                and ("створено" in response_message.lower()
                     or "created" in response_message.lower())
            )

            if not success_indicators:
                # Agent didn't create workout (maybe reached limit), create it here
                try:
                    from app.agents.tools.workout_tools import _create_workout_from_params_internal

                    collected = state.collected_parameters
                    workout_type = collected.get("type", "steady")
                    duration = collected.get("duration_minutes")
                    intensity = collected.get("intensity")

                    # Validate required parameters before calling
                    if not duration or not intensity:
                        logger.warning(
                            f"Cannot create workout: missing parameters. "
                            f"duration={duration}, intensity={intensity} for user {user_id}"
                        )
                        response_message = (
                            "Вибачте, мені потрібно знати тривалість та інтенсивність. "
                            "Можете повторити?"
                        )
                        needs_clarification = True
                    else:
                        genres_list = collected.get("genres", [])
                        genres_str = None
                        if genres_list:
                            if isinstance(genres_list, list):
                                genres_str = ",".join(genres_list)
                            else:
                                genres_str = str(genres_list)

                        result = _create_workout_from_params_internal(
                            user_id=user_id,
                            workout_type=workout_type,
                            duration_minutes=duration,
                            intensity=intensity,
                            genres=genres_str,
                            prompt=None,
                        )

                        if "error" not in result.lower():
                            # Parse workout object from result
                            if result.startswith("workout_created:"):
                                try:
                                    import json
                                    parts = result.split("|", 1)
                                    if len(parts) == 2:
                                        created_workout = json.loads(parts[1])
                                except Exception as e:
                                    logger.error(f"Failed to parse workout object: {e}")

                            response_message = "✅ Воркаут успішно створено! Тепер ви можете згенерувати плейлист."
                            is_complete = True
                            needs_clarification = False
                            logger.info(
                                f"Workout created via supervisor fallback for user {user_id}"
                            )
                        else:
                            response_message = f"Вибачте, не вдалося створити воркаут: {result}"
                            logger.error(
                                f"Failed to create workout via supervisor fallback: {result}"
                            )
                except Exception as e:
                    logger.error(
                        f"Error creating workout via supervisor fallback: {e}",
                        exc_info=True,
                    )
                    response_message = "Вибачте, виникла помилка при створенні воркауту. Спробуйте ще раз."

        # Check if workout was successfully created
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
                # Workout was successfully created - clear state and mark completed
                logger.info(
                    f"Workout created successfully for user {user_id}, "
                    f"clearing state"
                )
                await conversation_service.mark_conversation_completed(user_id)
                self.clear_state(user_id)
                is_complete = True
                needs_clarification = False
            else:
                logger.warning(
                    f"Workout creation reported success but contains error "
                    f"for user {user_id}, keeping state"
                )
        elif is_decline or any(
            word in response_message.lower()
            for word in ["скасовано", "canceled", "cancelled", "зрозуміло"]
        ):
            # User declined - clear state
            logger.info(
                f"Workout creation declined by user {user_id}, "
                f"clearing state"
            )
            self.clear_state(user_id)
            needs_clarification = False

        return ConversationUpdate(
            new_state=state,
            response_message=response_message,
            created_workout=created_workout,
            needs_clarification=needs_clarification,
            is_complete=is_complete,
        )

    def clear_state(self, user_id: str):
        """Clears the conversation state for a user."""
        if user_id in self.states:
            del self.states[user_id]
            logger.info(f"Cleared conversation state for user_id: {user_id}")


supervisor_agent = SupervisorAgent()
