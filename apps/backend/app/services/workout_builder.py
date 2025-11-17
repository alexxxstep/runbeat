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
from app.agents.tools.workout_tools import create_workout_from_params
from app.services.conversation_service import conversation_service


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

        # Tools for creating workouts
        # Note: AI agent now extracts parameters through prompt, not tools
        self.tools = [
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
            max_iterations=8,  # Increased to allow proper parameter extraction
            max_execution_time=25,  # 25 seconds to handle context + parameter extraction
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

        # CRITICAL: Extract and update parameters BEFORE building context
        # This ensures the agent always sees up-to-date collected_parameters
        self._update_collected_parameters_from_message(state, user_message)

        # Build comprehensive context for the AI agent (with user patterns)
        conversation_context = await self._build_conversation_context(state, user_message)

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

            # AI agent extracts parameters through prompt
            # Parameters are already extracted and saved in _update_collected_parameters_from_message()
            # But we do a final check to ensure nothing was missed

            # Final safety check: ensure parameters are still up-to-date
            # (This is a backup in case the message wasn't processed correctly earlier)
            if not state.collected_parameters.get("duration_minutes") or not state.collected_parameters.get("intensity"):
                # Re-extract if missing (shouldn't happen, but safety net)
                logger.debug(f"Re-extracting parameters for user {state.user_id} as safety check")
                self._update_collected_parameters_from_message(state, user_message)

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

    async def _build_conversation_context(self, state: ConversationState, user_message: str) -> str:
        """
        Build comprehensive context string for the AI agent.
        This context helps the agent understand what information is already collected
        and what still needs to be gathered. The agent uses this to make decisions.
        Includes user patterns for personalization.
        """
        collected = state.collected_parameters
        context_parts = []

        # User ID - CRITICAL for tool calls
        context_parts.append(f"User ID: {state.user_id}")

        # Current user message
        context_parts.append(f"Current user message: {user_message}")

        # User patterns for personalization
        try:
            patterns = await conversation_service.get_user_patterns(state.user_id)
            if patterns.get("has_history"):
                context_parts.append("\n## USER PREFERENCES (from history):")
                if "favorite_genres" in patterns:
                    genres_str = ", ".join(patterns["favorite_genres"])
                    context_parts.append(f"- Favorite genres: {genres_str}")
                if "typical_duration" in patterns:
                    context_parts.append(f"- Typical duration: ~{patterns['typical_duration']} minutes")
                if "preferred_type" in patterns:
                    context_parts.append(f"- Preferred workout type: {patterns['preferred_type']}")
                if "common_intensity" in patterns:
                    context_parts.append(f"- Common intensity: {patterns['common_intensity']}")
                context_parts.append("(Use these preferences to provide better suggestions)")
        except Exception as e:
            logger.debug(f"Could not fetch user patterns: {e}")

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

        # Current step indicator
        if not any(k in collected for k in ["duration_minutes", "intensity"]):
            current_step = "Step 1: Get duration and intensity"
        elif "genres" not in collected or not collected.get("genres"):
            current_step = "Step 2: Get music genres"
        else:
            current_step = "Step 3: Confirm and create workout"

        context_parts.append(f"\nCurrent step: {current_step}")

        # Instructions for the agent
        context_parts.append("\n---")
        context_parts.append("INSTRUCTIONS FOR THIS TURN:")
        context_parts.append(f"1. ANALYZE the user message: '{user_message}'")
        context_parts.append("2. EXTRACT parameters (duration, intensity, genres) from the message using your parser skills")
        context_parts.append("3. UPDATE collected_parameters by MERGING new info with existing (NEVER overwrite)")
        context_parts.append("4. CHECK 'Already collected' - NEVER ask for information you already have!")
        context_parts.append("5. If you have ALL required info → ask for FINAL confirmation")
        context_parts.append("6. If user confirms (да/так/yes/ok) → call create_workout_from_params tool")
        context_parts.append(f"7. CRITICAL: use user_id='{state.user_id}' when calling create_workout_from_params")
        context_parts.append("8. Respond in Ukrainian, keep it SHORT (1-2 sentences)")
        context_parts.append("\nREMEMBER: Look at chat_history above to see what user already told you!")

        return "\n".join(context_parts)

    def _update_collected_parameters_from_message(
        self, state: ConversationState, user_message: str
    ) -> None:
        """
        Extract parameters from user message and update state.collected_parameters.
        This ensures the agent always sees up-to-date collected parameters.

        Args:
            state: Conversation state to update
            user_message: Current user message to extract parameters from
        """
        collected = state.collected_parameters

        # Extract parameters from current message
        extracted_params = self._extract_parameters_from_user_message(user_message)

        # Also check recent history for missed parameters (last 3 user messages)
        if len(state.history) > 1:
            recent_user_messages = [
                msg["content"] for msg in state.history[-6:]
                if msg.get("role") == "user"
            ][-3:]  # Last 3 user messages

            for hist_msg in recent_user_messages:
                if hist_msg != user_message:  # Don't process current message twice
                    hist_params = self._extract_parameters_from_user_message(hist_msg)
                    # Merge with extracted params (don't overwrite existing)
                    for key, value in hist_params.items():
                        if key not in extracted_params:
                            extracted_params[key] = value
                        elif key == "genres":
                            # Accumulate genres
                            existing = extracted_params.get("genres", [])
                            new_genres = hist_params.get("genres", [])
                            if isinstance(existing, list) and isinstance(new_genres, list):
                                extracted_params["genres"] = list(set(existing + new_genres))

        # Update collected_parameters by merging (never overwrite existing values)
        for key, value in extracted_params.items():
            if key == "genres":
                # Accumulate genres (don't replace)
                existing_genres = collected.get("genres", [])
                new_genres = value if isinstance(value, list) else [value]
                if isinstance(existing_genres, list):
                    all_genres = list(set(existing_genres + new_genres))
                    collected["genres"] = all_genres
                else:
                    collected["genres"] = new_genres
            else:
                # Update other params if not already set, or if new value is more specific
                if key not in collected or not collected[key]:
                    collected[key] = value
                # For workout type, prefer more specific types (intervals > steady)
                elif key == "type" and value in ["intervals", "fartlek"] and collected.get("type") == "steady":
                    collected[key] = value

        logger.debug(
            f"Updated collected_parameters for user {state.user_id}: "
            f"extracted={extracted_params}, final={collected}"
        )

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

        # Parse workout type
        workout_type = None  # Don't set default yet
        if any(k in message_lower for k in ["інтервал", "interval", "інтервальн"]):
            workout_type = "intervals"
        elif any(k in message_lower for k in ["фартлек", "fartlek"]):
            workout_type = "fartlek"
        elif any(k in message_lower for k in ["відновлен", "recovery"]):
            workout_type = "steady"  # recovery maps to steady
        elif any(k in message_lower for k in ["біг", "пробіжк", "run", "running", "steady", "стабільн", "постійн"]):
            workout_type = "steady"

        # Set type if found, or if we have other workout parameters (use steady as default)
        if workout_type:
            params["type"] = workout_type
        elif params.get("duration_minutes") or params.get("intensity"):
            params["type"] = "steady"  # Default for regular runs

        # Parse genres with fuzzy matching
        genre_mapping = {
            # English genres
            "rock": ["rock", "рок", "рок-музик", "рок музик"],
            "pop": ["pop", "поп"],
            "electronic": ["electronic", "electric", "electro", "електро", "електронн", "електронну", "електроніка"],
            "classical": ["classic", "classical", "класик", "класична", "класичну"],
            "hip-hop": ["hip-hop", "hip hop", "хіп-хоп", "хіп хоп", "rap", "реп"],
            "jazz": ["jazz", "джаз"],
            "metal": ["metal", "метал"],
            "indie": ["indie", "інді"],
            "alternative": ["alternative", "альтернатив"],
            "dance": ["dance", "данс"],
            "house": ["house", "хаус"],
            "techno": ["techno", "техно", "в стилі техно", "техно стиль"],
            "trance": ["trance", "транс"],
            "reggae": ["reggae", "регі"],
            "country": ["country", "кантрі"],
            "r&b": ["r&b", "rnb", "r'n'b"],
            "blues": ["blues", "блюз"],
            "folk": ["folk", "фолк"],
            "ambient": ["ambient", "ембієнт", "chill"],
            "edm": ["edm", "едм"],
        }

        found_genres = []
        for genre, variations in genre_mapping.items():
            if any(var in message_lower for var in variations):
                found_genres.append(genre)

        # Special handling for phrases like "релаксну музику в стилі техно"
        # Check for "в стилі" or "in style" patterns
        style_patterns = [
            (r"в\s+стилі\s+(\w+)", "uk"),
            (r"in\s+style\s+(\w+)", "en"),
            (r"релаксну\s+музику\s+в\s+стилі\s+(\w+)", "uk"),
            (r"музику\s+в\s+стилі\s+(\w+)", "uk"),
        ]
        for pattern, lang in style_patterns:
            match = re.search(pattern, message_lower)
            if match:
                style_word = match.group(1).lower()
                # Try to match style word to a genre
                for genre, variations in genre_mapping.items():
                    if any(var in style_word or style_word in var for var in variations):
                        if genre not in found_genres:
                            found_genres.append(genre)
                        break

        if found_genres:
            params["genres"] = found_genres

        return params

    def _get_fallback_response(
        self, state: ConversationState, user_message: str
    ) -> str:
        """
        Fallback response when agent reaches iteration/time limit.
        Extracts parameters from current message and history, then generates response.
        """
        collected = state.collected_parameters
        message_lower = user_message.lower().strip()

        # CRITICAL: Extract parameters from current message when agent fails
        extracted_params = self._extract_parameters_from_user_message(user_message)

        # CRITICAL: Also check recent history for missed parameters
        if len(state.history) > 0:
            # Check last 3 user messages for parameters
            recent_user_messages = [
                msg["content"] for msg in state.history[-6:]
                if msg["role"] == "user"
            ][-3:]

            for hist_msg in recent_user_messages:
                hist_params = self._extract_parameters_from_user_message(hist_msg)
                # Merge with extracted params (don't overwrite existing)
                for key, value in hist_params.items():
                    if key not in extracted_params:
                        extracted_params[key] = value
                    elif key == "genres":
                        # Accumulate genres
                        existing = extracted_params.get("genres", [])
                        new_genres = hist_params.get("genres", [])
                        if isinstance(existing, list) and isinstance(new_genres, list):
                            extracted_params["genres"] = list(set(existing + new_genres))

        # Update collected_parameters with extracted params
        for key, value in extracted_params.items():
            if key == "genres":
                # Accumulate genres (don't replace)
                existing_genres = collected.get("genres", [])
                new_genres = value if isinstance(value, list) else [value]
                if isinstance(existing_genres, list):
                    all_genres = list(set(existing_genres + new_genres))
                    collected["genres"] = all_genres
                else:
                    collected["genres"] = new_genres
            else:
                # Update other params if not already set
                if key not in collected or not collected[key]:
                    collected[key] = value

        logger.debug(f"Fallback extracted params for user {state.user_id}: {extracted_params}")
        logger.debug(f"Updated collected_parameters: {collected}")

        # Check if we're waiting for confirmation and user responded
        if state.last_question == "final_confirmation":
            # Check for confirmation (yes/да/так)
            if any(
                word in message_lower
                for word in ["так", "yes", "да", "ок", "ok", "створ", "create"]
            ):
                # User confirmed - supervisor will create workout
                return "Добре! Створюю воркаут..."
            # Check for decline (no/ні)
            elif any(
                word in message_lower
                for word in ["ні", "no", "не треба", "не потрібно", "скасу", "cancel"]
            ):
                # User declined
                return "Зрозуміло! Якщо потрібна допомога ще - звертайся. Успішного тренування! 🏃‍♂️"

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
