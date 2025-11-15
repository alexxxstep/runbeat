"""
AI-powered workout builder using LangChain for natural conversation.
"""
from typing import Dict, Optional, Any
import json
from loguru import logger

from langchain.agents import AgentExecutor, create_structured_chat_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.schemas.conversation import ConversationState, ConversationUpdate, CurrentQuestion
from app.agents.base import BaseAgent
from app.agents.prompts.conversation_prompts import CONVERSATION_AGENT_SYSTEM_PROMPT
from app.agents.tools.parser_tools import rule_based_parse, validate_intent
from app.agents.tools.workout_tools import create_workout_from_params


class WorkoutBuilder(BaseAgent):
    """
    AI-powered workout builder agent that uses LangChain for natural conversation.
    Understands context, avoids loops, and helps users create workouts naturally.
    """

    def __init__(self):
        """Initialize WorkoutBuilder with LangChain agent."""
        super().__init__(
            temperature=0.7,  # Higher temperature for more natural conversation
            max_tokens=500,
            agent_type="conversation"
        )

        # Tools for parsing workout parameters and creating workouts
        self.tools = [
            rule_based_parse,
            validate_intent,
            create_workout_from_params,
        ]

        # Create prompt with tools
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", CONVERSATION_AGENT_SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}\n\n{agent_scratchpad}"),
        ])

        # Create agent
        self.agent = create_structured_chat_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt,
        )

        # Agent executor (memory will be managed per conversation)
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=False,
            handle_parsing_errors=True,
            max_iterations=10,  # Increased to handle complex conversations
            max_execution_time=30,  # 30 seconds max execution time
        )

        logger.info("WorkoutBuilder initialized with LangChain AI agent")

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
        Processes a user's message using AI agent and returns the response.
        All conversation logic is handled by the AI agent based on the prompt.
        """
        # Normalize and validate message
        user_message = user_message.strip()

        # Handle very short or unclear messages early (before calling agent)
        if len(user_message) <= 2 or user_message in ["+", "-", ".", "!", "?"]:
            logger.debug(
                f"Short/unclear message detected: '{user_message}' for user "
                f"{state.user_id}, using fallback"
            )
            # Use fallback response directly without calling agent
            fallback_response = self._get_fallback_response(state, user_message)
            state.history.append({"role": "user", "content": user_message})
            state.history.append({"role": "assistant", "content": fallback_response})
            state.last_question = self._determine_question_type_from_response(
                fallback_response, state
            )
            return ConversationUpdate(
                new_state=state, response_message=fallback_response
            )

        # Add user message to history
        state.history.append({"role": "user", "content": user_message})

        # Build comprehensive context for the AI agent
        conversation_context = self._build_conversation_context(state, user_message)

        try:
            # Create temporary memory from conversation history
            # Optimized: limit history to prevent memory overflow
            from langchain.memory import ConversationBufferMemory
            temp_memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True,
                max_token_limit=4000,  # Limit memory size
            )

            # Load history into memory (exclude current user message)
            # Keep only recent messages to avoid token limit issues
            recent_history = state.history[:-1]
            # Keep last 20 messages for context (prevents memory overflow)
            if len(recent_history) > 20:
                recent_history = recent_history[-20:]
                logger.debug(
                    f"Truncated history from {len(state.history)} to 20 messages "
                    f"for user {state.user_id}"
                )

            for msg in recent_history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "user":
                    temp_memory.chat_memory.add_user_message(content)
                elif role == "assistant":
                    temp_memory.chat_memory.add_ai_message(content)

            # Use AI agent to generate response - agent handles all logic via prompt
            # Wrap in error handler for retry logic
            from app.utils.openai_error_handler import OpenAIErrorHandler

            async def invoke_agent():
                return await self.agent_executor.ainvoke({
                    "input": conversation_context,
                    "chat_history": temp_memory.chat_memory.messages,
                })

            # Use retry logic for rate limits and timeouts
            response = await OpenAIErrorHandler.handle_with_retry(
                invoke_agent,
                max_retries=3,
                base_delay=1.0,
                max_delay=5.0
            )

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
                # Provide fallback response based on conversation state
                response_message = self._get_fallback_response(state, user_message)

            # Extract parameters from user message (fallback parsing)
            # The AI agent should handle this via tools, but we also parse as backup
            parsed_params = self._extract_parameters_from_user_message(user_message)
            if parsed_params:
                state.collected_parameters.update(parsed_params)

            # Determine question type based on response content
            state.last_question = self._determine_question_type_from_response(response_message, state)

            # Add assistant response to history
            state.history.append({"role": "assistant", "content": response_message})

            return ConversationUpdate(new_state=state, response_message=response_message)

        except Exception as e:
            logger.error(f"Error in WorkoutBuilder.process_message: {e}")

            # Import error handler
            from app.utils.openai_error_handler import OpenAIErrorHandler

            error_str = str(e).lower()

            # Check if it's an iteration/time limit error
            if (
                "iteration limit" in error_str
                or "time limit" in error_str
                or "stopped due to" in error_str
            ):
                logger.warning(
                    f"Agent reached iteration/time limit (exception) for user "
                    f"{state.user_id}. Message: {user_message}, Error: {error_str[:200]}"
                )
                # Use fallback response
                error_message = self._get_fallback_response(state, user_message)
            elif OpenAIErrorHandler.is_api_error(e):
                error_message = OpenAIErrorHandler.get_error_message(e)
                logger.warning(
                    f"OpenAI API error in WorkoutBuilder: {type(e).__name__} - {e}"
                )
            else:
                # Generic error message for non-API errors
                error_message = "Вибачте, виникла помилка. Спробуйте ще раз."
                logger.error(f"Unexpected error in WorkoutBuilder: {e}", exc_info=True)

            state.history.append({"role": "assistant", "content": error_message})
            return ConversationUpdate(new_state=state, response_message=error_message)

    def _build_conversation_context(self, state: ConversationState, user_message: str) -> str:
        """
        Build comprehensive context string for the AI agent.
        This context helps the agent understand what information is already collected
        and what still needs to be gathered. The agent uses this to make decisions.
        """
        collected = state.collected_parameters
        context_parts = []

        # User ID - CRITICAL for tool calls
        context_parts.append(f"User ID: {state.user_id}")

        # Current user message
        context_parts.append(f"Current user message: {user_message}")

        # What we already know (from previous messages)
        known_info = []
        if "duration_minutes" in collected:
            known_info.append(f"duration: {collected['duration_minutes']} minutes")
        if "intensity" in collected:
            intensity_map = {"low": "easy/low", "moderate": "moderate", "high": "hard/high/intense"}
            intensity_display = intensity_map.get(collected['intensity'], collected['intensity'])
            known_info.append(f"intensity: {intensity_display}")
        if "type" in collected:
            known_info.append(f"workout type: {collected['type']}")
        if "genres" in collected and collected["genres"]:
            genres_str = ", ".join(collected['genres'])
            known_info.append(f"music genres: {genres_str}")

        if known_info:
            context_parts.append(f"\nAlready collected: {', '.join(known_info)}")
        else:
            context_parts.append("\nAlready collected: nothing yet")

        # What we still need
        missing_info = []
        if "duration_minutes" not in collected:
            missing_info.append("duration (in minutes)")
        if "intensity" not in collected:
            missing_info.append("intensity (easy/low, moderate, or hard/high/intense)")
        if "genres" not in collected or not collected.get("genres"):
            missing_info.append("music preferences (at least one genre)")

        if missing_info:
            context_parts.append(f"\nStill need: {', '.join(missing_info)}")
        else:
            context_parts.append("\nStill need: nothing - ready for confirmation!")

        # Instructions for the agent
        context_parts.append("\n---")
        context_parts.append("Based on the conversation history above and this context, respond naturally.")
        context_parts.append("Use tools (rule_based_parse) to extract workout parameters from the user message.")
        context_parts.append("Check what you already know before asking questions.")
        context_parts.append("Move to the next step when you have enough information.")
        context_parts.append(f"IMPORTANT: When calling create_workout_from_params tool, use user_id='{state.user_id}'")

        return "\n".join(context_parts)

    def _extract_parameters_from_user_message(self, user_message: str) -> Dict:
        """
        Extract workout parameters from user message using simple rule-based parsing.
        This is a fallback - the AI agent should use rule_based_parse tool for better results.
        """
        params = {}
        message_lower = user_message.lower()

        # Parse duration
        import re
        duration_match = re.search(r'(\d+)\s*(хв|хвилин|min|minutes|год|hour)', message_lower)
        if duration_match:
            duration = int(duration_match.group(1))
            unit = duration_match.group(2).lower()
            if "год" in unit or "hour" in unit:
                duration = duration * 60  # Convert hours to minutes
            params["duration_minutes"] = duration

        # Parse intensity
        if any(k in message_lower for k in ["легк", "easy", "low", "recovery"]):
            params["intensity"] = "low"
        elif any(k in message_lower for k in ["середн", "moderate", "темпов", "tempo"]):
            params["intensity"] = "moderate"
        elif any(k in message_lower for k in ["важк", "висок", "high", "hard", "інтенсивн", "intense"]):
            params["intensity"] = "high"

        # Default workout type
        if params.get("duration_minutes") or params.get("intensity"):
            params["type"] = "steady"

        # Parse genres
        possible_genres = [
            "rock", "pop", "classic", "electronic", "рок", "поп", "класика", "електро",
            "hip-hop", "jazz", "metal", "indie", "alternative", "dance", "house", "techno",
            "reggae", "country", "r&b", "blues", "folk"
        ]
        found_genres = [g for g in possible_genres if g in message_lower]
        if found_genres:
            params["genres"] = found_genres

        return params

    def _get_fallback_response(
        self, state: ConversationState, user_message: str
    ) -> str:
        """
        Provide fallback response when agent reaches iteration/time limit.
        Uses rule-based logic to provide appropriate response based on state.
        """
        collected = state.collected_parameters.copy()  # Work with copy
        message_lower = user_message.lower().strip()

        # Try to extract parameters from user message first
        parsed_params = self._extract_parameters_from_user_message(user_message)
        if parsed_params:
            collected.update(parsed_params)
            # Update state's collected_parameters
            state.collected_parameters.update(parsed_params)

        # Refresh collected after potential updates
        collected = state.collected_parameters

        # Handle very short or unclear messages
        if len(message_lower) <= 2 or message_lower in ["+", "-", ".", "!", "?"]:
            # If we have some parameters, ask for what's missing
            if collected.get("duration_minutes") and collected.get("intensity"):
                genres = collected.get("genres")
                if not genres or (isinstance(genres, list) and len(genres) == 0):
                    return "Добре! Яку музику ти хочеш слухати під час тренування?"
            elif collected.get("duration_minutes") or collected.get("intensity"):
                return "Чудово! Яка планується тривалість та інтенсивність тренування?"
            else:
                return "Привіт! Я допоможу тобі створити ідеальне тренування. Яку пробіжку ти хочеш зробити?"

        # Check what we have and what we need
        has_duration = "duration_minutes" in collected
        has_intensity = "intensity" in collected
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
            intensity_map = {
                "low": "легка",
                "moderate": "середня",
                "high": "висока",
            }
            intensity_uk = intensity_map.get(
                collected.get("intensity", "moderate"), "середня"
            )
            genres_list = collected.get("genres", [])
            if isinstance(genres_list, list):
                genres_str = ", ".join(genres_list)
            else:
                genres_str = str(genres_list)
            return (
                f"Супер! Отже, {intensity_uk} пробіжка на {duration} хвилин "
                f"під {genres_str}. Створюємо воркаут?"
            )

    def _determine_question_type_from_response(
        self, response: str, state: ConversationState
    ) -> CurrentQuestion:
        """
        Determine what type of question we're asking based on response content.
        This helps track conversation state for the supervisor.
        """
        collected = state.collected_parameters
        response_lower = response.lower()

        # Check if asking for confirmation
        if any(k in response_lower for k in ["створ", "create", "підтверд", "confirm", "готов"]):
            return "final_confirmation"

        # Check if asking for genres
        if any(k in response_lower for k in ["музик", "music", "жанр", "genre", "плейлист"]):
            return "genres"

        # Check if asking for workout goal
        if any(k in response_lower for k in ["тривалість", "duration", "інтенсивність", "intensity", "скільки", "how long"]):
            return "goal_clarification"

        # Default based on what's missing
        if "genres" not in collected or not collected.get("genres"):
            return "genres"
        elif not all(k in collected for k in ["type", "duration_minutes", "intensity"]):
            return "goal_clarification"
        else:
            return "final_confirmation"
