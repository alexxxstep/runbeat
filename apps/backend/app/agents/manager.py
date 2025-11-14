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

            logger.info(f"WorkoutManagerAgent response: {response}")
            return response

        except Exception as e:
            logger.error(f"Error in WorkoutManagerAgent: {e}")
            return f"Error: Failed to create workout - {str(e)}"
