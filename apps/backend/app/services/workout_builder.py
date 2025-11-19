"""
AI-powered workout builder using LangChain for natural conversation.
Optimized version with extract_workout_parameters tool.
"""

from typing import Any, Dict, Optional
import json
from loguru import logger

from langchain.agents import AgentExecutor, create_structured_chat_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory

from app.schemas.conversation import ConversationState, ConversationUpdate, CurrentQuestion
from app.agents.base import BaseAgent
from app.agents.prompts.conversation_prompts import CONVERSATION_AGENT_SYSTEM_PROMPT
from app.agents.tools.workout_tools import create_workout_from_params
from app.agents.tools.parameter_extraction_tools import extract_workout_parameters
from app.models.workout import Workout


class WorkoutBuilder(BaseAgent):
    """
    AI-powered workout builder agent using LangChain.
    Uses extract_workout_parameters tool for parameter extraction.
    """

    def __init__(self):
        """Initialize WorkoutBuilder with LangChain agent and tools."""
        super().__init__(
            temperature=0.8,  # Higher temperature for more natural conversation
            max_tokens=500,
            agent_type="conversation",  # Uses OPENAI_MODEL_CONVERSATION from config
        )

        # Tools for the agent
        self.tools = [
            extract_workout_parameters,  # NEW: AI-driven parameter extraction
            create_workout_from_params,  # EXISTING: Workout creation
        ]

        # Create prompt with tools
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", CONVERSATION_AGENT_SYSTEM_PROMPT),
                MessagesPlaceholder(variable_name="chat_history", optional=True),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        # Create LangChain agent
        self.agent = create_structured_chat_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt,
        )

        # Custom error handler for tool validation errors
        def handle_error(error: Exception) -> str:
            """Handle parsing and validation errors gracefully."""
            error_str = str(error).lower()
            error_repr = repr(error).lower()
            error_type = type(error).__name__

            logger.warning(
                f"AgentExecutor error: {error} "
                f"(type: {error_type}, str: {error_str[:200]}, "
                f"repr: {error_repr[:200]})"
            )

            # Check if it's a Pydantic validation error related to workout parameters
            # The error might be formatted as "'duration', 'intensity'" or similar
            # Also check for common Pydantic validation error patterns
            is_validation_error = (
                ("duration" in error_str and "intensity" in error_str)
                or ("duration" in error_repr and "intensity" in error_repr)
                or ("'duration'" in error_str and "'intensity'" in error_str)
                or (
                    "missing" in error_str and ("duration" in error_str or "intensity" in error_str)
                )
                or (
                    "required" in error_str
                    and ("duration" in error_str or "intensity" in error_str)
                )
                or (
                    "validation" in error_str
                    and ("duration" in error_str or "intensity" in error_str)
                )
                or (
                    error_type in ["ValidationError", "ValueError"]
                    and ("duration" in error_str or "intensity" in error_str)
                )
            )

            if is_validation_error:
                logger.warning(
                    f"Pydantic validation error detected - agent tried to call "
                    f"create_workout_from_params without required parameters. "
                    f"Error type: {error_type}. Returning user-friendly message."
                )
                return (
                    "Вибачте, мені потрібно спочатку зібрати всі параметри. "
                    "Повідомте тривалість та інтенсивність тренування."
                )

            # Generic error handling
            logger.error(f"Unexpected error in AgentExecutor: {error_type} - {error}")
            return "Вибачте, виникла помилка. Можете повторити ваше запитання?"

        # Agent executor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,  # Enable for debugging
            handle_parsing_errors=handle_error,
            return_intermediate_steps=True,
            max_iterations=5,  # Reduced - agent should be more efficient now
            max_execution_time=20,  # 20 seconds timeout
        )

        logger.info(
            f"WorkoutBuilder initialized with {len(self.tools)} tools: "
            f"{[tool.name for tool in self.tools]}"
        )

    async def process(self, input_data: Any) -> Any:
        """
        Process input data (required by BaseAgent).

        Args:
            input_data: Tuple of (ConversationState, user_message)

        Returns:
            ConversationUpdate
        """
        if isinstance(input_data, tuple) and len(input_data) == 2:
            state, message = input_data
            return await self.process_message(state, message)
        else:
            raise ValueError("Input data must be a tuple of (ConversationState, user_message)")

    async def process_message(
        self, state: ConversationState, user_message: str
    ) -> ConversationUpdate:
        """
        Process user message using AI agent.

        Args:
            state: Current conversation state
            user_message: User's message

        Returns:
            ConversationUpdate with new state and response
        """
        # Normalize message
        user_message = user_message.strip()

        # Add user message to history
        state.history.append({"role": "user", "content": user_message})
        logger.info(
            f"[Conversation] user={state.user_id} -> '{user_message}' "
            f"(collected={state.collected_parameters})"
        )

        # Build context for the agent
        conversation_context = self._build_conversation_context(state, user_message)

        try:
            # Create temporary memory from conversation history
            temp_memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True,
                max_token_limit=4000,
            )

            # Load recent history into memory (last 15 messages)
            recent_history = state.history[:-1]  # Exclude current user message
            if len(recent_history) > 15:
                recent_history = recent_history[-15:]

            for msg in recent_history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "user":
                    temp_memory.chat_memory.add_user_message(content)
                elif role == "assistant":
                    temp_memory.chat_memory.add_ai_message(content)

            # Invoke AI agent
            from app.utils.openai_error_handler import OpenAIErrorHandler

            async def invoke_agent():
                try:
                    return await self.agent_executor.ainvoke(
                        {
                            "input": conversation_context,
                            "chat_history": temp_memory.chat_memory.messages,
                        }
                    )
                except Exception as e:
                    error_str = str(e).lower()
                    error_repr = repr(e).lower()
                    logger.error(
                        f"Error in agent_executor.ainvoke for user {state.user_id}: {error_str} "
                        f"(type: {type(e).__name__})",
                        exc_info=True,
                    )

                    # Check if it's a validation error related to workout parameters
                    # The error might be formatted as "'duration', 'intensity'" or similar
                    if (
                        ("duration" in error_str and "intensity" in error_str)
                        or ("duration" in error_repr and "intensity" in error_repr)
                        or ("'duration'" in error_str and "'intensity'" in error_str)
                    ):
                        logger.warning(
                            f"Validation error in agent execution - agent likely tried to create workout "
                            f"without all parameters. User: {state.user_id}"
                        )
                        # Return a response that will trigger fallback
                        return {
                            "output": "Вибачте, мені потрібно спочатку зібрати всі параметри. "
                            "Повідомте тривалість та інтенсивність тренування."
                        }

                    # Re-raise other errors
                    raise

            # Use retry logic for rate limits
            response = await OpenAIErrorHandler.handle_with_retry(
                invoke_agent, max_retries=3, base_delay=1.0, max_delay=5.0
            )

            intermediate_steps = response.get("intermediate_steps", [])
            created_workout: Optional[dict] = None

            response_message = response.get("output", "Вибачте, я не зрозумів. Можете повторити?")

            # Check if agent stopped due to iteration/time limit
            response_lower = response_message.lower()
            if (
                "iteration limit" in response_lower
                or "time limit" in response_lower
                or "stopped due to" in response_lower
            ):
                logger.warning(
                    f"Agent reached iteration/time limit for user {state.user_id}. "
                    f"Message: {user_message}, Response: {response_message[:100]}"
                )
                response_message = self._get_fallback_response(state, user_message)

            # Determine question type based on response
            state.last_question = self._determine_question_type_from_response(
                response_message, state
            )

            # Add assistant response to history
            state.history.append({"role": "assistant", "content": response_message})

            # Process intermediate tool steps to update collected parameters or detect workout creation
            created_workout = self._process_tool_steps(
                state=state,
                steps=intermediate_steps,
                user_message=user_message,
            ) or created_workout

            has_duration = bool(state.collected_parameters.get("duration_minutes"))
            has_intensity = bool(state.collected_parameters.get("intensity"))
            genres = state.collected_parameters.get("genres")
            has_genres = bool(genres) and isinstance(genres, list)

            needs_clarification = not (has_duration and has_intensity and has_genres)
            is_complete = created_workout is not None

            if is_complete:
                needs_clarification = False

            logger.info(
                f"[Conversation] user={state.user_id} <- '{response_message[:120]}' "
                f"(needs_clarification={needs_clarification}, is_complete={is_complete})"
            )

            return ConversationUpdate(
                new_state=state,
                response_message=response_message,
                created_workout=created_workout,
                needs_clarification=needs_clarification,
                is_complete=is_complete,
            )

        except Exception as e:
            error_str = str(e).lower()
            error_repr = repr(e).lower()
            logger.error(
                f"Error in WorkoutBuilder.process_message for user {state.user_id}: {error_str} "
                f"(type: {type(e).__name__})",
                exc_info=True,
            )

            from app.utils.openai_error_handler import OpenAIErrorHandler

            # Check if it's a Pydantic validation error related to workout parameters
            # The error might be formatted as "'duration', 'intensity'" or similar
            if (
                ("duration" in error_str and "intensity" in error_str)
                or ("duration" in error_repr and "intensity" in error_repr)
                or ("'duration'" in error_str and "'intensity'" in error_str)
            ):
                logger.warning(
                    f"Validation error detected - likely agent tried to create workout without all parameters. "
                    f"User: {state.user_id}, Message: {user_message[:50]}"
                )
                # Use fallback response
                error_message = self._get_fallback_response(state, user_message)
            elif OpenAIErrorHandler.is_api_error(e):
                error_message = OpenAIErrorHandler.get_error_message(e)
                logger.warning(f"OpenAI API error in WorkoutBuilder: {type(e).__name__} - {e}")
            else:
                error_message = "Вибачте, виникла помилка. Спробуйте ще раз."
                logger.error(f"Unexpected error in WorkoutBuilder: {e}", exc_info=True)

            state.history.append({"role": "assistant", "content": error_message})
            return ConversationUpdate(
                new_state=state,
                response_message=error_message,
                needs_clarification=True,
            )

    def _process_tool_steps(
        self,
        state: ConversationState,
        steps: Any,
        user_message: str,
    ) -> Optional[dict]:
        """
        Inspect intermediate tool steps to keep ConversationState in sync with AI reasoning.
        """
        created_workout: Optional[dict] = None
        if not steps:
            return None

        collected = state.collected_parameters.copy()

        for step in steps:
            if not isinstance(step, (list, tuple)) or len(step) != 2:
                continue

            action, observation = step
            tool_name = getattr(action, "tool", "") or getattr(action, "name", "")
            observation_str = (
                observation
                if isinstance(observation, str)
                else json.dumps(observation, ensure_ascii=False)
            )

            if tool_name == extract_workout_parameters.name:
                extracted = self._safe_json_loads(observation_str)
                if not extracted:
                    continue

                collected = self._merge_collected_parameters(collected, extracted)
                state.collected_parameters = collected

                if extracted.get("all_collected"):
                    state.last_question = "final_confirmation"

                logger.info(
                    f"[Conversation] user={state.user_id} parameters updated -> {state.collected_parameters}"
                )

            elif tool_name == create_workout_from_params.name:
                workout_data = self._parse_workout_creation(observation_str)
                if workout_data:
                    created_workout = workout_data
                    collected = {}
                    state.collected_parameters = {}
                    state.last_question = "none"
                    duration = workout_data.get("duration_minutes")
                    intensity = workout_data.get("intensity")
                    hr_zones = workout_data.get("hr_zones") or [110, 180]
                    if duration and intensity:
                        try:
                            state.active_workout = Workout(
                                id=workout_data.get("id"),
                                type=workout_data.get("type", "steady"),
                                duration_minutes=duration,
                                intensity=intensity,
                                hr_zones=hr_zones,
                                confidence=0.95,
                                needs_clarification=False,
                            )
                        except Exception as exc:
                            logger.warning(
                                f"Failed to set active workout for user {state.user_id}: {exc}"
                            )

                    logger.info(
                        f"[Conversation] user={state.user_id} workout created via tool "
                        f"(id={workout_data.get('id')})"
                    )

        state.collected_parameters = collected
        return created_workout

    @staticmethod
    def _merge_collected_parameters(current: Dict[str, Any], extracted: Dict[str, Any]) -> Dict[str, Any]:
        merged = current.copy()

        for key in ["duration_minutes", "intensity", "workout_type"]:
            value = extracted.get(key)
            if value:
                merged[key] = value

        if "genres" in extracted and extracted["genres"]:
            existing = merged.get("genres", [])
            if not isinstance(existing, list):
                existing = []
            merged["genres"] = list({*existing, *extracted["genres"]})

        if extracted.get("clarification_question"):
            merged["clarification_question"] = extracted["clarification_question"]

        return merged

    @staticmethod
    def _parse_workout_creation(observation: str) -> Optional[dict]:
        text = observation.strip()
        if text.startswith("error"):
            logger.warning(f"Workout creation tool returned error: {text}")
            return None

        if text.startswith("workout_created:"):
            parts = text.split("|", 1)
            if len(parts) == 2:
                return WorkoutBuilder._safe_json_loads(parts[1])
        elif text.startswith("{"):
            return WorkoutBuilder._safe_json_loads(text)

        return None

    @staticmethod
    def _safe_json_loads(payload: str) -> Optional[dict]:
        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            logger.warning(f"Failed to decode JSON payload: {payload[:120]}")
            return None

    def _build_conversation_context(self, state: ConversationState, user_message: str) -> str:
        """
        Build context string for the AI agent.
        This context helps the agent understand what information is already collected.
        """
        collected = state.collected_parameters
        context_parts = []

        # User ID - CRITICAL for tool calls
        context_parts.append(f"User ID: {state.user_id}")

        # Current user message
        context_parts.append(f"Current user message: {user_message}")

        # Already collected parameters
        context_parts.append(f"\nAlready collected parameters:")
        context_parts.append(json.dumps(collected, indent=2, ensure_ascii=False))

        # Conversation history (last 10 messages for context)
        recent_history = state.history[-10:] if len(state.history) > 10 else state.history
        context_parts.append(f"\nConversation history (last {len(recent_history)} messages):")
        context_parts.append(json.dumps(recent_history, indent=2, ensure_ascii=False))

        # Instructions for this turn
        context_parts.append("\n---")
        context_parts.append("YOUR TASK FOR THIS TURN:")
        context_parts.append("1. Call extract_workout_parameters tool to analyze user message")
        context_parts.append("2. Check what parameters are now collected")
        context_parts.append("3. Respond naturally in Ukrainian")
        context_parts.append("4. Guide user to next step if info is missing")
        context_parts.append("5. If all collected → ask for confirmation")
        context_parts.append("6. If user confirms → call create_workout_from_params tool")
        context_parts.append(
            f"7. CRITICAL: use user_id='{state.user_id}' when calling create_workout_from_params"
        )

        return "\n".join(context_parts)

    def _get_fallback_response(self, state: ConversationState, user_message: str) -> str:
        """
        Fallback response when agent reaches iteration/time limit or errors occur.
        """
        collected = state.collected_parameters
        message_lower = user_message.lower().strip()

        # Check if waiting for confirmation
        if state.last_question == "final_confirmation":
            if any(
                word in message_lower
                for word in ["так", "yes", "да", "ок", "ok", "створ", "create"]
            ):
                return "Добре! Створюю воркаут..."
            elif any(word in message_lower for word in ["ні", "no", "не треба", "скасу"]):
                return "Зрозуміло! Якщо потрібна допомога ще - звертайся. Успішного тренування! 🏃‍♂️"

        # Check what we have and what we need
        has_duration = "duration_minutes" in collected and collected["duration_minutes"]
        has_intensity = "intensity" in collected and collected["intensity"]
        has_genres = (
            "genres" in collected
            and collected.get("genres")
            and len(collected.get("genres", [])) > 0
        )

        # Provide appropriate response based on what's missing
        if not has_duration or not has_intensity:
            return (
                "Чудово! Яка планується тривалість та інтенсивність тренування? "
                "(наприклад: легка пробіжка 30 хвилин)"
            )
        elif not has_genres:
            return (
                "Добре! А яку музику ти хочеш слухати під час тренування? "
                "Можна назвати кілька жанрів."
            )
        else:
            # We have everything, ask for confirmation
            duration = collected.get("duration_minutes", 30)
            intensity_map = {"low": "легка", "moderate": "середня", "high": "висока"}
            intensity_uk = intensity_map.get(collected.get("intensity", "moderate"), "середня")
            genres_list = collected.get("genres", [])
            genres_str = (
                ", ".join(genres_list) if isinstance(genres_list, list) else str(genres_list)
            )

            return (
                f"Супер! Отже, {intensity_uk} пробіжка на {duration} хвилин "
                f"під {genres_str}. Створюємо воркаут?"
            )

    def _determine_question_type_from_response(
        self, response: str, state: ConversationState
    ) -> CurrentQuestion:
        """
        Determine what type of question we're asking based on response content.
        """
        collected = state.collected_parameters
        response_lower = response.lower()

        # Check if asking for confirmation
        if any(k in response_lower for k in ["створ", "create", "підтверд", "confirm"]):
            return "final_confirmation"

        # Check if asking for genres
        if any(k in response_lower for k in ["музик", "music", "жанр", "genre"]):
            return "genres"

        # Check if asking for workout goal
        if any(
            k in response_lower for k in ["тривалість", "duration", "інтенсивність", "intensity"]
        ):
            return "goal_clarification"

        # Default based on what's missing
        if "genres" not in collected or not collected.get("genres"):
            return "genres"
        elif not all(k in collected for k in ["duration_minutes", "intensity"]):
            return "goal_clarification"
        else:
            return "final_confirmation"
