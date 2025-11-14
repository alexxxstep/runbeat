"""
Workout Manager Agent using LangChain.
"""
from typing import Optional, Dict, Any
import json
from loguru import logger

from langchain.agents import AgentExecutor, create_structured_chat_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.agents.base import BaseAgent
from app.agents.tools.workout_tools import (
    create_workout,
    activate_workout,
    get_active_workout,
)
from app.agents.prompts.manager_prompts import (
    MANAGER_AGENT_SYSTEM_PROMPT,
    MANAGER_AGENT_USER_PROMPT_TEMPLATE,
)
from app.schemas.llm_responses import WorkoutIntent


class WorkoutManagerAgent(BaseAgent):
    """
    LangChain-based workout manager agent.

    Handles workout creation and activation in the database.
    """

    def __init__(self):
        """Initialize WorkoutManagerAgent."""
        super().__init__(temperature=0.3, max_tokens=200)  # Precise and reliable
        self.output_parser = None  # Returns success/error messages

        # Tools
        self.tools = [
            create_workout,
            activate_workout,
            get_active_workout,
        ]

        # Prompt (must include {tools}, {tool_names}, and {agent_scratchpad})
        # Format matches other agents (parser, conversation, curator)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", MANAGER_AGENT_SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}\n\n{agent_scratchpad}"),
        ])

        # Agent
        self.agent = create_structured_chat_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt,
        )

        # Agent executor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            memory=self.memory,
            verbose=False,
            handle_parsing_errors=True,
            max_iterations=3,
        )

        logger.info("WorkoutManagerAgent initialized with LangChain")

    async def process(self, input_data: Dict[str, Any]) -> str:
        """
        Process workout management request.

        Args:
            input_data: Dict with 'user_id', 'workout_intent'

        Returns:
            Success message with workout_id or error message
        """
        user_id = input_data.get("user_id")
        workout_intent = input_data.get("workout_intent")

        return await self.create_and_activate_workout(
            user_id=user_id,
            workout_intent=workout_intent,
        )

    async def create_and_activate_workout(
        self,
        user_id: str,
        workout_intent: WorkoutIntent,
    ) -> str:
        """
        Create and activate workout.

        Args:
            user_id: User ID
            workout_intent: Workout intent

        Returns:
            Success message with workout_id or error message
        """
        logger.info(
            f"Creating workout for user {user_id}: "
            f"{workout_intent.workout_type}, {workout_intent.duration_minutes} min"
        )

        # Build user prompt
        workout_intent_json = workout_intent.model_dump_json()
        user_prompt = MANAGER_AGENT_USER_PROMPT_TEMPLATE.format(
            user_id=user_id,
            workout_intent_json=workout_intent_json,
        )

        try:
            # Invoke agent
            result = await self.agent_executor.ainvoke({
                "input": user_prompt,
            })

            # Extract output
            response = result.get("output", "")

            # Check if agent stopped due to iteration/time limit
            if "iteration limit" in response.lower() or "time limit" in response.lower():
                logger.warning("WorkoutManagerAgent reached iteration/time limit, using fallback")
                # Try to create and activate workout directly using tools
                return await self._create_and_activate_workout_fallback(user_id, workout_intent)

            logger.info(f"WorkoutManagerAgent response: {response}")
            return response

        except Exception as e:
            error_str = str(e)
            logger.error(f"Error in WorkoutManagerAgent: {e}")

            # Check if it's an iteration/time limit error
            if "iteration limit" in error_str.lower() or "time limit" in error_str.lower():
                logger.warning("WorkoutManagerAgent exception indicates iteration/time limit, using fallback")
                return await self._create_and_activate_workout_fallback(user_id, workout_intent)

            return f"Error: Failed to create workout - {str(e)}"

    async def _create_and_activate_workout_fallback(
        self,
        user_id: str,
        workout_intent: WorkoutIntent,
    ) -> str:
        """
        Fallback method to create and activate workout directly using tools.
        Used when agent reaches iteration/time limit.

        Args:
            user_id: User ID
            workout_intent: Workout intent

        Returns:
            Success message with workout_id or error message
        """
        try:
            logger.info("Using fallback method to create and activate workout")

            # First, check if workout was already created (agent might have created it before hitting limit)
            from app.agents.tools.workout_tools import get_active_workout, activate_workout
            from app.services.supabase_service import supabase_service
            import json
            from datetime import datetime, timedelta

            # Check for active workout first
            active_workout_result = get_active_workout(user_id)
            if active_workout_result and active_workout_result != "none" and not active_workout_result.startswith("error"):
                try:
                    active_workout = json.loads(active_workout_result)
                    workout_id = active_workout.get("id")
                    if workout_id:
                        logger.info(f"Found existing active workout {workout_id}, returning it")
                        return f"Workout created and activated. ID: {workout_id}"
                except Exception:
                    pass

            # Check for recently created workout (within last 30 seconds) that might not be activated
            try:
                client = supabase_service.get_client()
                # Try to select without is_active first, then check if column exists
                recent_workouts = (
                    client.table("workouts")
                    .select("id, created_at")
                    .eq("user_id", user_id)
                    .order("created_at", desc=True)
                    .limit(1)
                    .execute()
                )

                if recent_workouts.data and len(recent_workouts.data) > 0:
                    recent_workout = recent_workouts.data[0]
                    created_at_str = recent_workout.get("created_at")
                    if created_at_str:
                        created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                        time_diff = (datetime.now(created_at.tzinfo) - created_at).total_seconds()

                        # If workout was created within last 30 seconds, try to activate it
                        if time_diff < 30:
                            workout_id = recent_workout.get("id")

                            if workout_id:
                                # Try to activate the workout
                                logger.info(f"Found recently created workout {workout_id}, activating it")
                                activation_result = activate_workout(workout_id, user_id)
                                if activation_result == "success":
                                    return f"Workout created and activated. ID: {workout_id}"
                                else:
                                    logger.warning(f"Failed to activate existing workout {workout_id}: {activation_result}")
                                    # Continue to create new workout
            except Exception as e:
                error_dict = e if isinstance(e, dict) else {"message": str(e)}
                # Check if error is about missing column
                if error_dict.get("code") == "42703" or "does not exist" in str(e).lower():
                    logger.debug("is_active column does not exist, skipping recent workout check")
                else:
                    logger.debug(f"Could not check for recent workouts: {e}")
                # Continue to create new workout

            # Create workout using tool
            workout_intent_json = workout_intent.model_dump_json()
            workout_id_result = create_workout(user_id, workout_intent_json)

            # Check if creation was successful
            # create_workout returns either workout_id (UUID string) or "error: <message>"
            if not workout_id_result or workout_id_result.startswith("error"):
                logger.error(f"Failed to create workout: {workout_id_result}")
                return workout_id_result if workout_id_result else "error: Failed to create workout - no response"

            workout_id = workout_id_result  # This is the workout ID string

            # Activate workout
            activation_result = activate_workout(workout_id, user_id)

            if activation_result == "success":
                logger.info(f"Successfully created and activated workout {workout_id} using fallback")
                return f"Workout created and activated. ID: {workout_id}"
            else:
                logger.warning(f"Workout {workout_id} created but activation failed: {activation_result}")
                # Workout was created, so return success even if activation had issues
                return f"Workout created. ID: {workout_id} (Note: Activation may have failed: {activation_result})"

        except Exception as e:
            logger.error(f"Error in fallback workout creation: {e}", exc_info=True)
            # Ensure we return a string, not an exception object
            error_message = str(e) if e else "Unknown error"
            return f"Error: Failed to create workout - {error_message}"
