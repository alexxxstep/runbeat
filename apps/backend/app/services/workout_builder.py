"""
AI-powered workout builder using LangChain for natural conversation.
Optimized version with extract_workout_parameters tool.
"""

from typing import Any, Dict, Optional, List
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

        # Auto-extract parameters every turn to keep state in sync
        self._auto_extract_parameters(state=state, user_message=user_message)
        # Capture optional prompt answers when applicable
        prompt_captured = self._capture_prompt_response_if_needed(
            state=state, user_message=user_message
        )

        if prompt_captured:
            response_message = self._build_prompt_ack_response(state)
            state.last_question = "final_confirmation"
            state.history.append({"role": "assistant", "content": response_message})
            logger.info(
                f"[Conversation] user={state.user_id} <- '{response_message[:120]}' "
                "(needs_clarification=False, is_complete=False)"
            )
            return ConversationUpdate(
                new_state=state,
                response_message=response_message,
                created_workout=None,
                needs_clarification=False,
                is_complete=False,
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

            missing = self._missing_parameters(state.collected_parameters)
            needs_clarification = any(
                missing[key] for key in ["duration", "intensity", "genres", "duration_invalid", "intensity_invalid"]
            )
            is_complete = created_workout is not None

            if state.last_question == "final_confirmation" and not is_complete:
                needs_clarification = False
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
                    if self._needs_optional_prompt(collected):
                        state.last_question = "prompt"
                    else:
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
                                prompt=workout_data.get("prompt"),
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

    def _auto_extract_parameters(self, state: ConversationState, user_message: str) -> None:
        """
        Run extract_workout_parameters tool on every user turn to keep state fresh,
        even if the agent fails to call the tool.
        """
        if not user_message:
            return

        try:
            history_slice = state.history[-10:]
            history_json = json.dumps(history_slice, ensure_ascii=False)
            params_json = json.dumps(state.collected_parameters, ensure_ascii=False)
            tool_input = {
                "user_message": user_message,
                "conversation_history": history_json,
                "current_params": params_json,
            }
            raw = extract_workout_parameters.invoke(tool_input)
            extracted = self._safe_json_loads(raw)
            if not extracted:
                return

            merged = self._merge_collected_parameters(state.collected_parameters, extracted)
            state.collected_parameters = merged

            if extracted.get("all_collected"):
                if self._needs_optional_prompt(merged):
                    state.last_question = "prompt"
                else:
                    state.last_question = "final_confirmation"

            logger.info(
                f"[Conversation] user={state.user_id} params auto-update -> {state.collected_parameters}"
            )
        except Exception as exc:
            logger.warning(
                f"Auto parameter extraction failed for user {state.user_id}: {exc}"
            )

    def _capture_prompt_response_if_needed(
        self, state: ConversationState, user_message: str
    ) -> bool:
        """
        Store optional music/style prompt when the previous assistant turn asked for it.
        """
        if state.last_question != "prompt":
            return False

        cleaned = (user_message or "").strip()
        if not cleaned:
            return False

        lower = cleaned.lower()
        negative_keywords = [
            "нема",
            "немає",
            "без побаж",
            "нічого",
            "none",
            "skip",
        ]
        confirmation_keywords = ["створ", "згенер", "ок", "yes", "да", "так"]

        # If user says there are no extra wishes, just mark prompt as checked
        if any(keyword in lower for keyword in negative_keywords):
            state.collected_parameters.pop("prompt", None)
            state.collected_parameters["_prompt_checked"] = True
            return True

        # If user rushed to confirmation words, do not treat as prompt but mark as checked
        if any(keyword in lower for keyword in confirmation_keywords):
            state.collected_parameters["_prompt_checked"] = True
            return True

        # Save trimmed prompt (limit to avoid extremely long strings)
        state.collected_parameters["prompt"] = cleaned[:400]
        state.collected_parameters["_prompt_checked"] = True
        return True

    def _build_prompt_ack_response(self, state: ConversationState) -> str:
        collected = state.collected_parameters
        prompt_text = collected.get("prompt") or "без уточнень"
        duration = collected.get("duration_minutes")
        intensity = collected.get("intensity")
        genres = collected.get("genres", [])

        duration_part = f"{duration} хвилин" if duration else "обрану тривалість"
        intensity_map = {"low": "легку 😊", "moderate": "середню 💪", "high": "високу ⚡️"}
        intensity_part = intensity_map.get(intensity, "обрану інтенсивність")
        genres_part = ""
        if genres:
            display_genres = ", ".join(self._display_genre_name(g) for g in genres)
            genres_part = f" під {display_genres}"

        return (
            f"🎨 Записав атмосферу: {prompt_text}. "
            f"Готові завершити {intensity_part} пробіжку на {duration_part}{genres_part}? "
            "Створюємо воркаут?"
        )

    @staticmethod
    def _merge_collected_parameters(current: Dict[str, Any], extracted: Dict[str, Any]) -> Dict[str, Any]:
        merged = current.copy()

        if "duration_minutes" in extracted:
            normalized = WorkoutBuilder._normalize_duration(extracted["duration_minutes"])
            if normalized is not None:
                merged["duration_minutes"] = normalized
                merged.pop("_duration_invalid", None)
                else:
                merged.pop("duration_minutes", None)
                merged["_duration_invalid"] = extracted["duration_minutes"]

        if "intensity" in extracted:
            normalized_intensity = WorkoutBuilder._normalize_intensity(extracted["intensity"])
            if normalized_intensity:
                merged["intensity"] = normalized_intensity
                merged.pop("_intensity_invalid", None)
            else:
                merged.pop("intensity", None)
                merged["_intensity_invalid"] = extracted["intensity"]

        if "workout_type" in extracted and extracted["workout_type"]:
            merged["workout_type"] = extracted["workout_type"]

        if "genres" in extracted and extracted["genres"]:
            normalized_genres = WorkoutBuilder._normalize_genres(extracted["genres"])
            if normalized_genres:
                existing = merged.get("genres", [])
                if not isinstance(existing, list):
                    existing = []
                merged["genres"] = list(dict.fromkeys(existing + normalized_genres))

        if extracted.get("clarification_question"):
            merged["clarification_question"] = extracted["clarification_question"]

        return merged

    @staticmethod
    def _normalize_duration(value: Any) -> Optional[int]:
        try:
            minutes = int(float(value))
        except (TypeError, ValueError):
            return None
        if 5 <= minutes <= 180:
            return minutes
        return None

    @staticmethod
    def _normalize_intensity(value: Any) -> Optional[str]:
        if not isinstance(value, str):
            return None
        normalized = value.strip().lower()
        mapping = {
            "легка": "low",
            "easy": "low",
            "низька": "low",
            "recovery": "low",
            "середня": "moderate",
            "темпова": "moderate",
            "moderate": "moderate",
            "tempo": "moderate",
            "висока": "high",
            "hard": "high",
            "high": "high",
            "інтенсивна": "high",
        }
        if normalized in ["low", "moderate", "high"]:
            return normalized
        return mapping.get(normalized)

    @staticmethod
    def _normalize_genres(genres: Any) -> List[str]:
        normalized: List[str] = []
        if isinstance(genres, str):
            genres_iter = [genres]
        elif isinstance(genres, list):
            genres_iter = genres
        else:
            genres_iter = []

        genre_map = {
            "electronic": ["electronic", "electric", "electro", "електро", "електронн", "едм", "edm"],
            "rock": ["rock", "рок"],
            "pop": ["pop", "поп"],
            "classical": ["classic", "classical", "класик", "класична", "класичну"],
            "hip-hop": ["hip-hop", "hip hop", "хіп-хоп", "реп", "rap"],
            "jazz": ["jazz", "джаз"],
            "metal": ["metal", "метал"],
            "indie": ["indie", "інді"],
            "alternative": ["alternative", "альтернатив"],
            "dance": ["dance", "данс"],
            "house": ["house", "хаус"],
            "techno": ["techno", "техно"],
            "trance": ["trance", "транс"],
            "reggae": ["reggae", "регі"],
            "country": ["country", "кантрі"],
            "blues": ["blues", "блюз"],
            "folk": ["folk", "фолк"],
            "ambient": ["ambient", "ембієнт", "chill", "релакс"],
            "r&b": ["r&b", "rnb"],
        }

        for genre in genres_iter:
            if not isinstance(genre, str):
                continue
            genre_lower = genre.lower()
            matched = None
            for canonical, variations in genre_map.items():
                if any(var in genre_lower for var in variations):
                    matched = canonical
                        break
            normalized.append(matched or genre_lower)
        return normalized

    @staticmethod
    def _display_genre_name(genre: str) -> str:
        display_map = {
            "rock": "рок",
            "pop": "поп",
            "classical": "класика",
            "hip-hop": "хіп-хоп",
            "jazz": "джаз",
            "metal": "метал",
            "indie": "інді",
            "alternative": "альтернатива",
            "dance": "денс",
            "house": "хаус",
            "techno": "техно",
            "trance": "транс",
            "reggae": "реггі",
            "country": "кантрі",
            "blues": "блюз",
            "folk": "фолк",
            "ambient": "ембієнт",
            "r&b": "R&B",
            "drum-and-bass": "drum & bass",
            "latin": "латина",
            "electronic": "електроніка",
        }
        return display_map.get(genre, genre)

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
        context_parts.append(
            "5. Once duration + intensity + genres are collected, ask ONE short question about optional wishes "
            "(atmosphere/mood/extra hints) and store the answer in `prompt` (or mark that there are none)."
        )
        context_parts.append("6. If everything is ready → summarize and ask for confirmation")
        context_parts.append("7. If user confirms → call create_workout_from_params tool")
        context_parts.append(
            f"8. CRITICAL: use user_id='{state.user_id}' when calling create_workout_from_params"
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

        missing_prompt = self._format_missing_prompt(collected, state)
        if missing_prompt:
            return missing_prompt

            # We have everything, ask for confirmation
            duration = collected.get("duration_minutes", 30)
        intensity_map = {"low": "легка 😊", "moderate": "середня 💪", "high": "висока ⚡️"}
        intensity_uk = intensity_map.get(collected.get("intensity", "moderate"), "середня 💪")
            genres_list = collected.get("genres", [])
            if isinstance(genres_list, list):
            genres_str = ", ".join(self._display_genre_name(g) for g in genres_list)
            else:
                genres_str = str(genres_list)
        prompt_text = collected.get("prompt")
        prompt_suffix = ""
        if isinstance(prompt_text, str) and prompt_text.strip():
            prompt_suffix = f" Атмосфера: {prompt_text.strip()}."

        state.last_question = "final_confirmation"
            return (
                f"Супер! Отже, {intensity_uk} пробіжка на {duration} хвилин "
            f"під {genres_str}.{prompt_suffix} Створюємо воркаут?"
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

        # Check if asking for optional prompt / vibe
        prompt_keywords = [
            "побаж",
            "атмосфер",
            "настр",
            "опис",
            "віб",
            "додатков",
            "prompt",
        ]
        if any(k in response_lower for k in prompt_keywords):
            return "prompt"

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
        elif self._needs_optional_prompt(collected):
            return "prompt"
        else:
            return "final_confirmation"

    def _missing_parameters(self, collected: Dict[str, Any]) -> Dict[str, bool]:
        return {
            "duration": not bool(collected.get("duration_minutes")),
            "intensity": not bool(collected.get("intensity")),
            "genres": not (collected.get("genres") and isinstance(collected.get("genres"), list)),
            "duration_invalid": "_duration_invalid" in collected,
            "intensity_invalid": "_intensity_invalid" in collected,
        }

    @staticmethod
    def _needs_optional_prompt(collected: Dict[str, Any]) -> bool:
        """Check whether we should ask about optional music/vibe prompt."""
        has_duration = bool(collected.get("duration_minutes"))
        has_intensity = bool(collected.get("intensity"))
        genres = collected.get("genres")
        has_genres = isinstance(genres, list) and bool(genres)
        has_core = has_duration and has_intensity and has_genres

        if not has_core:
            return False

        prompt_value = collected.get("prompt")
        prompt_checked = bool(collected.get("_prompt_checked"))
        has_prompt_text = isinstance(prompt_value, str) and prompt_value.strip() != ""

        return not prompt_checked and not has_prompt_text

    def _format_missing_prompt(
        self, collected: Dict[str, Any], state: ConversationState
    ) -> Optional[str]:
        missing = self._missing_parameters(collected)

        if missing["duration_invalid"]:
            invalid_value = collected.get("_duration_invalid")
            state.last_question = "duration"
            return (
                f"⏱️ Тривалість має бути в межах 5–300 хвилин. Зараз вказано {invalid_value}. "
                "Спробуй, будь ласка, 20, 30 чи 45 хв."
            )

        if missing["intensity_invalid"]:
            state.last_question = "intensity"
            return "💪 Яку інтенсивність оберемо? Легка 😊, середня 💪 чи висока ⚡️?"

        if self._needs_optional_prompt(collected):
            state.last_question = "prompt"
            return (
                "🌈 У нас вже є тривалість, інтенсивність і музика! "
                "Маєш побажання до атмосфери чи улюблених виконавців? "
                "Наприклад: 'нічний синтвейв 🌌', 'рок з жіночим вокалом 🎤'. "
                "Якщо без додаткових побажань — просто скажи про це."
            )

        duration_missing = missing["duration"]
        intensity_missing = missing["intensity"]
        genres_missing = missing["genres"]

        if duration_missing and intensity_missing and genres_missing:
            state.last_question = "duration"
            return (
                "👋 Розкажи, скільки хвилин і з яким темпом плануєш бігти "
                "(наприклад 30 хв + легка 😊 чи 40 хв + середня 💪), "
                "а ще напиши 1–2 жанри для плейлиста 🎶 (рок 🤘, поп 💃, electro ⚡️)."
            )

        if duration_missing and intensity_missing:
            state.last_question = "duration"
            return (
                "⏱️ Скільки хвилин та якою буде інтенсивність? "
                "Приклади: 25 хв + легка 😊, 40 хв + середня 💪, 30 хв + висока ⚡️."
            )

        if duration_missing:
            state.last_question = "duration"
            return (
                f"⏱️ {('Маємо ' + (collected.get('intensity') or 'обрану інтенсивність'))}. "
                "Скільки хвилин плануєш бігти? Наприклад 20, 30 чи 45 хв."
            )

        if intensity_missing:
            state.last_question = "intensity"
            duration = collected.get("duration_minutes")
            duration_txt = f"{duration} хв" if duration else "тренування"
            return (
                f"💪 {duration_txt} — чудово! Обери інтенсивність: легка 😊, середня 💪 чи висока ⚡️."
            )

        if genres_missing:
            state.last_question = "genres"
            return (
                "🎵 Яку музику або виконавців ставимо? Напиши, наприклад: рок 🤘, поп 💃, techno ⚡️ чи улюбленого артиста."
            )

        return None
