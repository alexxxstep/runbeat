"""
Conversation Manager for RunBeat.
Handles multi-turn conversations with context and state management.
"""
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from loguru import logger
from datetime import datetime
from uuid import uuid4

from app.schemas.llm_responses import WorkoutIntent, PlaylistResponse
from app.services.llm_service import LLMService
from app.services.supabase_service import supabase_service
from app.services.spotify_service import SpotifyService
from app.services.prompts.prompt_builder import ConversationState, UserContext
from app.services.workout_parser_agent import WorkoutParserAgent as LegacyWorkoutParserAgent
from app.core.config import settings

# Conditional import for LangChain agents
LANGCHAIN_AVAILABLE = False
LangChainWorkoutParserAgent = None
LangChainMusicCuratorAgent = None
ConversationAgent = None
ConversationOrchestrator = None

if settings.USE_LANGCHAIN_PARSER:
    try:
        from app.agents.parser import WorkoutParserAgent as LangChainWorkoutParserAgent
        LANGCHAIN_AVAILABLE = True
        logger.info("LangChain WorkoutParserAgent imported successfully")
    except ImportError as e:
        logger.warning(f"LangChain not available, using legacy parser: {e}")
        LANGCHAIN_AVAILABLE = False
        LangChainWorkoutParserAgent = None

if settings.USE_LANGCHAIN_CURATOR:
    try:
        from app.agents.curator import MusicCuratorAgent as LangChainMusicCuratorAgent
        logger.info("LangChain MusicCuratorAgent imported successfully")
    except ImportError as e:
        logger.warning(f"LangChain MusicCuratorAgent not available: {e}")
        LangChainMusicCuratorAgent = None

# Always try to import ConversationAgent for handling greetings and general questions
try:
    from app.agents.conversation import ConversationAgent
    logger.info("ConversationAgent imported successfully")
except ImportError as e:
    logger.warning(f"ConversationAgent not available: {e}")
    ConversationAgent = None

# Import ConversationOrchestrator (Supervisor) if enabled
if settings.USE_LANGCHAIN_SUPERVISOR:
    try:
        from app.agents.supervisor import ConversationOrchestrator
        logger.info("ConversationOrchestrator (Supervisor) imported successfully")
    except ImportError as e:
        logger.warning(f"ConversationOrchestrator not available: {e}")
        ConversationOrchestrator = None


class ConversationStateEnum(str, Enum):
    """States in conversation flow."""

    NEW = "new"
    PARSING_INTENT = "parsing_intent"
    NEEDS_CLARIFICATION = "needs_clarification"
    ASK_WORKOUT_CONFIRMATION = "ask_workout_confirmation"  # New: Asking user to confirm workout creation
    READY_TO_GENERATE = "ready_to_generate"
    GENERATING_PLAYLIST = "generating_playlist"
    COMPLETE = "complete"
    ERROR = "error"


class ConversationAction(str, Enum):
    """Actions conversation manager can take."""

    PARSE_INTENT = "parse_intent"
    ASK_CLARIFICATION = "ask_clarification"
    ASK_WORKOUT_CONFIRMATION = "ask_workout_confirmation"  # New: Ask user to confirm workout creation
    CREATE_WORKOUT = "create_workout"  # New: Create workout in database
    GENERATE_PLAYLIST = "generate_playlist"
    SHOW_PLAYLIST = "show_playlist"
    ERROR_RESPONSE = "error_response"


class ConversationResponse:
    """Response from conversation manager."""

    def __init__(
        self,
        message: str,
        workout_intent: Optional[WorkoutIntent] = None,
        needs_clarification: bool = False,
        conversation_id: Optional[str] = None,
        is_complete: bool = False,
    ):
        self.message = message
        self.workout_intent = workout_intent
        self.needs_clarification = needs_clarification
        self.conversation_id = conversation_id
        self.is_complete = is_complete


class ConversationManager:
    """
    Manages multi-turn conversations for workout playlist generation.

    Handles:
    - Context preservation across messages
    - Intelligent follow-up questions
    - State machine for conversation flow
    - Decision making (when to generate playlist)
    """

    def __init__(
        self,
        llm_service: Optional[LLMService] = None,
        spotify_service: Optional[SpotifyService] = None,
        parser_agent: Optional[Any] = None,  # Can be LegacyWorkoutParserAgent or LangChainWorkoutParserAgent
    ):
        """
        Initialize conversation manager.

        Args:
            llm_service: LLM service for parsing and generation (creates new if not provided)
            spotify_service: Spotify service for creating playlists (creates new if not provided)
            parser_agent: Workout parser agent (creates new if not provided)
        """
        self.llm_service = llm_service or LLMService()
        self.spotify_service = spotify_service or SpotifyService()

        # Choose parser agent based on feature flag
        if parser_agent:
            self.parser_agent = parser_agent
            self.use_langchain_parser = False
        elif settings.USE_LANGCHAIN_PARSER and LANGCHAIN_AVAILABLE:
            self.parser_agent = LangChainWorkoutParserAgent()
            self.use_langchain_parser = True
            logger.info("Using LangChain WorkoutParserAgent")
        else:
            self.parser_agent = LegacyWorkoutParserAgent(self.llm_service)
            self.use_langchain_parser = False
            logger.info("Using legacy WorkoutParserAgent")

        # Choose curator agent based on feature flag
        if settings.USE_LANGCHAIN_CURATOR and LangChainMusicCuratorAgent:
            self.curator_agent = LangChainMusicCuratorAgent()
            self.use_langchain_curator = True
            logger.info("Using LangChain MusicCuratorAgent")
        else:
            self.curator_agent = None
            self.use_langchain_curator = False
            logger.info("Using legacy LLMService for playlist generation")

        # Initialize ConversationAgent for handling greetings and general questions
        if ConversationAgent:
            try:
                self.conversation_agent = ConversationAgent()
                logger.info("ConversationAgent initialized for handling greetings and general questions")
            except Exception as e:
                logger.warning(f"Failed to initialize ConversationAgent: {e}")
                self.conversation_agent = None
        else:
            self.conversation_agent = None
            logger.info("ConversationAgent not available")

        # Initialize ConversationOrchestrator (Supervisor) if enabled
        if settings.USE_LANGCHAIN_SUPERVISOR and ConversationOrchestrator:
            try:
                self.orchestrator = ConversationOrchestrator()
                self.use_supervisor = True
                logger.info("ConversationOrchestrator (Supervisor) initialized - using full LangChain multi-agent system")
            except Exception as e:
                logger.warning(f"Failed to initialize ConversationOrchestrator: {e}")
                self.orchestrator = None
                self.use_supervisor = False
        else:
            self.orchestrator = None
            self.use_supervisor = False
            logger.info("ConversationOrchestrator not enabled - using direct agent integration")

        self.conversations: Dict[str, Dict[str, Any]] = {}
        logger.info("ConversationManager initialized")

    async def process_message(
        self,
        user_id: str,
        message: str,
        conversation_id: Optional[str] = None,
        user_preferences: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Process user message and determine next action.

        Args:
            user_id: User identifier
            message: User's message text
            conversation_id: Existing conversation ID (if continuing)
            user_preferences: User's saved preferences

        Returns:
            Tuple of (conversation_id, response_data)

        Response data contains:
            - state: Current conversation state
            - action: Action to take
            - workout_intent: Parsed intent (if ready)
            - clarification_question: Question to ask (if needed)
            - playlist: Generated playlist (if complete)
            - message_to_user: Message to display to user
        """
        try:
            # Get or create conversation
            if conversation_id:
                conversation = await self._load_conversation(conversation_id, user_id)
                if not conversation:
                    logger.warning(
                        f"Conversation {conversation_id} not found, creating new one"
                    )
                    conversation_id = None
            else:
                conversation = None

            if not conversation_id:
                conversation_id = self._create_conversation(user_id)
                conversation = self.conversations[conversation_id]
                logger.info(f"Started new conversation {conversation_id}")

            # Add user message to history
            conversation["messages"].append(
                {
                    "role": "user",
                    "content": message,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

            # Determine current state and next action
            current_state = conversation.get("state", ConversationStateEnum.NEW)
            logger.debug(f"Current state: {current_state}")

            # If Supervisor (ConversationOrchestrator) is enabled, use it for full multi-agent orchestration
            if self.use_supervisor and self.orchestrator:
                logger.info("Using ConversationOrchestrator (Supervisor) for message processing")
                try:
                    # Convert conversation state to format expected by orchestrator
                    orchestrator_state = {
                        "state": current_state.value if isinstance(current_state, ConversationStateEnum) else current_state,
                        "workout_intent": conversation.get("workout_intent"),
                        "workout_id": conversation.get("workout_id"),
                        "messages": conversation.get("messages", [])[:-1],  # Exclude current message
                    }

                    # Process through orchestrator
                    orchestrator_response = await self.orchestrator.process_message(
                        user_id=user_id,
                        message=message,
                        conversation_state=orchestrator_state,
                        user_preferences=user_preferences,
                    )

                    # Convert orchestrator response to ConversationManager format
                    # Map orchestrator state to ConversationStateEnum
                    state_mapping = {
                        "new": ConversationStateEnum.NEW,
                        "needs_clarification": ConversationStateEnum.NEEDS_CLARIFICATION,
                        "intent_ready": ConversationStateEnum.PARSING_INTENT,
                        "workout_confirmation": ConversationStateEnum.ASK_WORKOUT_CONFIRMATION,
                        "workout_created": ConversationStateEnum.COMPLETE,
                        "complete": ConversationStateEnum.COMPLETE,
                    }

                    mapped_state = state_mapping.get(
                        orchestrator_response.get("state", "new"),
                        ConversationStateEnum.NEEDS_CLARIFICATION
                    )

                    # Update conversation with orchestrator response
                    conversation["state"] = mapped_state.value
                    conversation["workout_intent"] = orchestrator_response.get("workout_intent")
                    conversation["workout_id"] = orchestrator_response.get("workout_id")
                    if orchestrator_response.get("message_to_user"):
                        conversation["messages"].append({
                            "role": "assistant",
                            "content": orchestrator_response["message_to_user"],
                            "timestamp": datetime.utcnow().isoformat(),
                        })
                    conversation["updated_at"] = datetime.utcnow().isoformat()

                    # Save conversation
                    await self._save_conversation(conversation)

                    # Map action
                    action_mapping = {
                        "ask_clarification": ConversationAction.ASK_CLARIFICATION,
                        "ask_confirmation": ConversationAction.ASK_WORKOUT_CONFIRMATION,
                        "workout_created": ConversationAction.CREATE_WORKOUT,
                        "generate_playlist": ConversationAction.GENERATE_PLAYLIST,
                    }

                    mapped_action = action_mapping.get(
                        orchestrator_response.get("action", "ask_clarification"),
                        ConversationAction.ASK_CLARIFICATION
                    )

                    return conversation_id, {
                        "state": mapped_state,
                        "action": mapped_action,
                        "message_to_user": orchestrator_response.get("message_to_user", ""),
                        "workout_intent": orchestrator_response.get("workout_intent"),
                        "workout_id": orchestrator_response.get("workout_id"),
                        "playlist": orchestrator_response.get("playlist"),
                    }
                except Exception as e:
                    logger.error(f"Error in ConversationOrchestrator: {e}", exc_info=True)
                    # Fall through to normal processing

            # Check if message is a greeting or general question (not workout-related)
            # Use ConversationAgent if available
            if self.conversation_agent and self._is_greeting_or_general_question(message, current_state):
                logger.info(f"Detected greeting/general question: '{message}', using ConversationAgent")
                try:
                    # Use ConversationAgent to handle the message
                    response = await self.conversation_agent.respond(
                        message=message,
                        user_id=user_id,
                        conversation_history=conversation["messages"][:-1],  # Exclude current message
                        user_preferences=user_preferences,
                    )

                    # Add assistant response to history
                    conversation["messages"].append(
                        {
                            "role": "assistant",
                            "content": response,
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )

                    # Keep state as NEW or NEEDS_CLARIFICATION (don't change to workout-related states)
                    conversation["state"] = ConversationStateEnum.NEEDS_CLARIFICATION
                    conversation["updated_at"] = datetime.utcnow().isoformat()

                    # Save conversation
                    await self._save_conversation(conversation)

                    return conversation_id, {
                        "state": ConversationStateEnum.NEEDS_CLARIFICATION,
                        "action": ConversationAction.ASK_CLARIFICATION,
                        "message_to_user": response,
                        "workout_intent": None,
                    }
                except Exception as e:
                    logger.error(f"Error in ConversationAgent: {e}")
                    # Fall through to normal processing

            # Check if user is responding to workout confirmation question
            if current_state == ConversationStateEnum.ASK_WORKOUT_CONFIRMATION:
                # User is responding to "Створити воркаут? Да/Ні"
                confirmation_response = await self._handle_workout_confirmation(
                    message=message,
                    conversation=conversation,
                    user_id=user_id,
                )
                if confirmation_response:
                    # Update conversation state
                    conversation["state"] = confirmation_response["state"]
                    conversation["updated_at"] = datetime.utcnow().isoformat()

                    # Add assistant response to history
                    if confirmation_response.get("message_to_user"):
                        conversation["messages"].append(
                            {
                                "role": "assistant",
                                "content": confirmation_response["message_to_user"],
                                "timestamp": datetime.utcnow().isoformat(),
                            }
                        )

                    # Save conversation
                    await self._save_conversation(conversation)

                    return conversation_id, confirmation_response

            # Parse user intent
            workout_intent = await self._parse_user_intent(
                message=message,
                conversation_history=conversation["messages"],
                user_preferences=user_preferences,
            )

            # Update conversation with parsed intent
            conversation["workout_intent"] = (
                workout_intent.model_dump() if workout_intent else None
            )

            # Decide next action based on intent and state
            action, response_data = await self._decide_next_action(
                conversation=conversation,
                workout_intent=workout_intent,
                user_preferences=user_preferences,
            )

            # Update conversation state
            conversation["state"] = response_data["state"]
            conversation["updated_at"] = datetime.utcnow().isoformat()

            # Add assistant response to history
            if response_data.get("message_to_user"):
                conversation["messages"].append(
                    {
                        "role": "assistant",
                        "content": response_data["message_to_user"],
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )

            # Save conversation to database
            await self._save_conversation(conversation)

            logger.info(
                f"Conversation {conversation_id}: "
                f"state={response_data['state']}, action={response_data['action']}"
            )

            return conversation_id, response_data

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return conversation_id or "error", {
                "state": ConversationStateEnum.ERROR,
                "action": ConversationAction.ERROR_RESPONSE,
                "message_to_user": "Вибачте, виникла помилка. Спробуйте ще раз.",
                "error": str(e),
            }

    async def _parse_user_intent(
        self,
        message: str,
        conversation_history: List[Dict[str, str]],
        user_preferences: Optional[Dict[str, Any]],
    ) -> Optional[WorkoutIntent]:
        """
        Parse user intent from message with conversation context.

        Args:
            message: Current user message
            conversation_history: Full conversation history
            user_preferences: User preferences

        Returns:
            WorkoutIntent if parsing successful, None otherwise
        """
        try:
            # Build conversation history for LLM (OpenAI format)
            llm_history = [
                {"role": msg["role"], "content": msg["content"]}
                for msg in conversation_history[:-1]  # Exclude current message
            ]

            # Build UserContext
            user_context = UserContext(
                user_id=None,  # Will be set from conversation
                language="uk",
            )

            # Use WorkoutParserAgent (hybrid: rule-based + AI)
            if self.use_langchain_parser:
                # LangChain agent expects different format
                intent = await self.parser_agent.parse(
                    message=message,
                    conversation_history=conversation_history,
                )
            else:
                # Legacy agent
                intent = await self.parser_agent.parse(
                    message=message,
                    conversation_history=conversation_history,
                    user_context=user_context,
                )

            # Log parsed intent for debugging
            logger.info(
                f"Parsed intent from '{message}': "
                f"type={intent.workout_type}, "
                f"duration={intent.duration_minutes}, "
                f"bpm={intent.target_bpm_min}-{intent.target_bpm_max}, "
                f"confidence={intent.confidence}, "
                f"needs_clarification={intent.needs_clarification}"
            )

            return intent

        except Exception as e:
            logger.error(f"Failed to parse intent from message '{message}': {e}")
            return None

    async def _decide_next_action(
        self,
        conversation: Dict[str, Any],
        workout_intent: Optional[WorkoutIntent],
        user_preferences: Optional[Dict[str, Any]],
    ) -> Tuple[ConversationAction, Dict[str, Any]]:
        """
        Decide next action based on conversation state and parsed intent.

        Args:
            conversation: Current conversation data
            workout_intent: Parsed workout intent
            user_preferences: User preferences

        Returns:
            Tuple of (action, response_data)
        """
        if not workout_intent:
            # Failed to parse intent - ask for clarification
            return ConversationAction.ASK_CLARIFICATION, {
                "state": ConversationStateEnum.NEEDS_CLARIFICATION,
                "action": ConversationAction.ASK_CLARIFICATION,
                "message_to_user": "Не зовсім зрозумів. Опиши тренування детальніше: скільки часу і яка інтенсівність?",
                "workout_intent": None,
            }

        # Check if clarification needed (LLM flagged this)
        # BUT: If intent is actually complete (has all required fields), ignore needs_clarification flag
        is_complete = self._is_intent_complete(workout_intent)
        logger.debug(
            f"Intent completeness check: needs_clarification={workout_intent.needs_clarification}, "
            f"is_complete={is_complete}, confidence={workout_intent.confidence}"
        )

        if workout_intent.needs_clarification and not is_complete:
            logger.info("Asking for clarification based on LLM flag")
            return ConversationAction.ASK_CLARIFICATION, {
                "state": ConversationStateEnum.NEEDS_CLARIFICATION,
                "action": ConversationAction.ASK_CLARIFICATION,
                "message_to_user": workout_intent.clarification_question
                or "Можете уточнити деталі тренування?",
                "workout_intent": workout_intent.model_dump(),
                "confidence": workout_intent.confidence,
            }

        # Check if intent is complete enough to ask for workout confirmation
        if self._is_intent_complete(workout_intent):
            # Intent is complete - ask user to confirm workout creation
            logger.info("Intent complete, asking for workout confirmation...")

            # Format workout summary for user
            workout_summary = self._format_workout_summary(workout_intent)
            confirmation_message = (
                f"Ось що я зрозумів про твоє тренування:\n\n{workout_summary}\n\n"
                "Створити воркаут? (Да/Ні)"
            )

            return ConversationAction.ASK_WORKOUT_CONFIRMATION, {
                "state": ConversationStateEnum.ASK_WORKOUT_CONFIRMATION,
                "action": ConversationAction.ASK_WORKOUT_CONFIRMATION,
                "message_to_user": confirmation_message,
                    "workout_intent": workout_intent.model_dump(),
                "confidence": workout_intent.confidence,
                }
        else:
            # Intent not complete - ask follow-up
            follow_up = self._generate_follow_up_question(workout_intent, conversation)

            return ConversationAction.ASK_CLARIFICATION, {
                "state": ConversationStateEnum.NEEDS_CLARIFICATION,
                "action": ConversationAction.ASK_CLARIFICATION,
                "message_to_user": follow_up,
                "workout_intent": workout_intent.model_dump(),
                "confidence": workout_intent.confidence,
            }

    def _is_greeting_or_general_question(self, message: str, current_state: ConversationStateEnum) -> bool:
        """
        Check if message is a greeting or general question (not workout-related).

        Args:
            message: User's message
            current_state: Current conversation state

        Returns:
            True if message is greeting/general question, False if workout-related
        """
        message_lower = message.lower().strip()

        # If state is NEW, check for greetings
        if current_state == ConversationStateEnum.NEW:
            greetings = [
                "привіт", "вітаю", "добрий день", "добрий вечір", "доброго ранку",
                "hello", "hi", "hey", "вітаю", "здоров", "здоровенькі були",
            ]
            if any(greeting in message_lower for greeting in greetings):
                return True

        # Check for general questions
        general_questions = [
            "ти хто", "хто ти", "що ти", "що це", "як це працює", "як працює",
            "допомога", "help", "що ти вмієш", "що можеш", "можливості",
            "who are you", "what are you", "what is this", "how does this work",
        ]
        if any(question in message_lower for question in general_questions):
            return True

        # Check if message is very short and doesn't contain workout keywords
        workout_keywords = [
            "біг", "пробіжка", "тренування", "воркаут", "workout", "run", "running",
            "хвилин", "хв", "година", "години", "minutes", "hour", "hours",
            "інтервали", "фартлек", "темповий", "легкий", "важкий", "інтенсивність",
            "intervals", "fartlek", "tempo", "easy", "hard", "intensity",
        ]

        # If message is short (< 20 chars) and doesn't contain workout keywords, might be greeting/question
        if len(message_lower) < 20 and not any(keyword in message_lower for keyword in workout_keywords):
            # But check if it's clearly a workout description
            if any(char.isdigit() for char in message_lower):  # Contains numbers - might be workout
                return False
            return True

        return False

    def _is_intent_complete(self, intent: WorkoutIntent) -> bool:
        """
        Check if workout intent has all required info to generate playlist.

        Args:
            intent: Parsed workout intent

        Returns:
            True if complete, False if needs more info
        """
        # Basic requirements
        if not intent.workout_type:
            return False

        if not intent.duration_minutes or intent.duration_minutes < 5:
            return False

        if not intent.target_bpm_min or not intent.target_bpm_max:
            return False

        # Confidence threshold - lowered to 0.6 to be more permissive
        # If all required fields are present, accept even with lower confidence
        if intent.confidence < 0.6:
            logger.debug(f"Intent confidence too low: {intent.confidence}")
            return False

        # If confidence is between 0.6-0.7 but all fields are present, accept it
        if intent.confidence >= 0.6 and intent.confidence < 0.7:
            logger.debug(f"Intent confidence moderate ({intent.confidence}), but all fields present - accepting")

        # Interval-specific requirements
        if intent.workout_type == "intervals":
            if not intent.intervals or len(intent.intervals) == 0:
                return False

        return True

    def _generate_follow_up_question(
        self, intent: WorkoutIntent, conversation: Dict[str, Any]
    ) -> str:
        """
        Generate intelligent follow-up question based on missing info.

        Args:
            intent: Partially complete workout intent
            conversation: Current conversation state

        Returns:
            Follow-up question string
        """
        # Use LLM-generated question if available
        if intent.clarification_question:
            return intent.clarification_question

        # Check conversation history to avoid repetitive questions
        previous_questions = [
            msg.get("content", "")
            for msg in conversation.get("messages", [])
            if msg.get("role") == "assistant"
        ]

        # Duration missing or unclear
        if not intent.duration_minutes or intent.duration_minutes < 5:
            if not any("час" in q.lower() or "хвилин" in q.lower() for q in previous_questions):
                return "Скільки часу плануєш бігти? (наприклад: 30 хв, година)"

        # Intensity unclear (BPM not set properly)
        if intent.confidence < 0.7:
            if not any("інтенсивність" in q.lower() for q in previous_questions):
                return "Яка інтенсивність - легкий біг, темповий чи інтервали?"

        # Interval pattern missing
        if intent.workout_type == "intervals" and not intent.intervals:
            if not any("інтервал" in q.lower() for q in previous_questions):
                return "Який інтервал роботи/відпочинку? (наприклад: 5-2, це 5 хв робота / 2 хв відпочинок)"

        # Generic fallback
        return "Опиши тренування трохи детальніше, щоб я зрозумів краще."

    def _format_workout_summary(self, intent: WorkoutIntent) -> str:
        """
        Format workout intent into user-friendly summary.

        Args:
            intent: Workout intent to format

        Returns:
            Formatted summary string
        """
        workout_type_map = {
            "continuous": "Стабільна пробіжка",
            "intervals": "Інтервальна пробіжка",
            "fartlek": "Фартлек",
            "recovery": "Відновлювальна пробіжка",
        }

        intensity_map = {
            "steady": "легка",
            "building": "помірна",
            "wave": "помірна",
        }

        workout_type = workout_type_map.get(intent.workout_type, "Пробіжка")
        # Map energy_profile to intensity description
        if intent.target_bpm_min < 120:
            intensity_desc = "легка"
        elif intent.target_bpm_min < 150:
            intensity_desc = "помірна"
        else:
            intensity_desc = "висока"

        summary = f"🏃 **{workout_type}**\n"
        summary += f"⏱️ Тривалість: {intent.duration_minutes} хвилин\n"
        summary += f"⚡ Інтенсивність: {intensity_desc}\n"
        summary += f"🎵 BPM: {intent.target_bpm_min}-{intent.target_bpm_max}"

        if intent.intervals:
            summary += f"\n🔄 Інтервали: {len(intent.intervals)}"

        return summary

    async def _handle_workout_confirmation(
        self,
        message: str,
        conversation: Dict[str, Any],
        user_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Handle user's response to workout confirmation question.

        Args:
            message: User's response (Да/Ні/Yes/No)
            conversation: Current conversation
            user_id: User ID

        Returns:
            Response data if handled, None otherwise
        """
        # Normalize message for checking
        message_lower = message.lower().strip()

        # Check for positive confirmation
        positive_responses = ["да", "так", "yes", "y", "ok", "ок", "створ", "створити", "зроби", "зробити"]
        negative_responses = ["ні", "no", "n", "не", "не треба", "не потрібно", "скасувати", "відмінити"]

        is_positive = any(response in message_lower for response in positive_responses)
        is_negative = any(response in message_lower for response in negative_responses)

        if not is_positive and not is_negative:
            # Unclear response - ask again
            return {
                "state": ConversationStateEnum.ASK_WORKOUT_CONFIRMATION,
                "action": ConversationAction.ASK_WORKOUT_CONFIRMATION,
                "message_to_user": "Не зовсім зрозумів. Будь ласка, відповідь 'Да' або 'Ні'. Створити воркаут?",
                "workout_intent": conversation.get("workout_intent"),
            }

        if is_positive:
            # User confirmed - create workout
            try:
                workout_intent_dict = conversation.get("workout_intent")
                if not workout_intent_dict:
                    return {
                        "state": ConversationStateEnum.ERROR,
                        "action": ConversationAction.ERROR_RESPONSE,
                        "message_to_user": "Вибачте, не вдалось знайти дані про тренування. Спробуйте ще раз.",
                    }

                workout_intent = WorkoutIntent(**workout_intent_dict)
                workout_id = await self._create_workout_in_db(
                    user_id=user_id,
                    workout_intent=workout_intent,
                )

                if workout_id:
                    return {
                        "state": ConversationStateEnum.COMPLETE,
                        "action": ConversationAction.CREATE_WORKOUT,
                        "message_to_user": (
                            f"✅ Воркаут успішно створено!\n\n"
                            f"Ти можеш почати тренування або згенерувати плейлист для нього. "
                            f"Якщо будуть якісь побажання - звертайся!"
                        ),
                        "workout_intent": workout_intent_dict,
                        "workout_id": workout_id,
                    }
                else:
                    return {
                        "state": ConversationStateEnum.ERROR,
                        "action": ConversationAction.ERROR_RESPONSE,
                        "message_to_user": "Вибачте, не вдалось створити воркаут. Спробуйте ще раз.",
                    }
            except Exception as e:
                logger.error(f"Failed to create workout: {e}")
                return {
                    "state": ConversationStateEnum.ERROR,
                    "action": ConversationAction.ERROR_RESPONSE,
                    "message_to_user": "Вибачте, виникла помилка при створенні воркауту. Спробуйте ще раз.",
                }

        else:  # is_negative
            # User declined - end conversation politely
            return {
                "state": ConversationStateEnum.COMPLETE,
                "action": ConversationAction.ASK_CLARIFICATION,
                "message_to_user": (
                    "Зрозуміло! Якщо будуть якісь побажання або запитань - звертайся. "
                    "Готовий допомогти з тренуваннями! 💪"
                ),
                "workout_intent": None,
            }

    async def _create_workout_in_db(
        self,
        user_id: str,
        workout_intent: WorkoutIntent,
    ) -> Optional[str]:
        """
        Create workout in database.

        Args:
            user_id: User ID
            workout_intent: Parsed workout intent

        Returns:
            Workout ID if created successfully, None otherwise
        """
        try:
            client = supabase_service.get_client()

            # Map energy_profile to intensity
            # energy_profile: "steady", "building", "wave"
            # intensity: "low", "moderate", "high"
            if workout_intent.target_bpm_min < 120:
                intensity = "low"
            elif workout_intent.target_bpm_min < 150:
                intensity = "moderate"
            else:
                intensity = "high"

            # Map workout_type from WorkoutIntent to database type
            # WorkoutIntent: "continuous", "intervals", "fartlek", "recovery"
            # Database: "steady", "progressive", "intervals", "fartlek"
            type_mapping = {
                "continuous": "steady",
                "intervals": "intervals",
                "fartlek": "fartlek",
                "recovery": "steady",
            }
            db_workout_type = type_mapping.get(workout_intent.workout_type, "steady")

            # Convert WorkoutIntent to workout data
            workout_data = {
                "user_id": user_id,
                "type": db_workout_type,
                "duration_minutes": workout_intent.duration_minutes,
                "intensity": intensity,
                "hr_zones": [workout_intent.target_bpm_min, workout_intent.target_bpm_max],
            }

            # Add optional fields
            if workout_intent.intervals:
                interval_stages = []
                for interval in workout_intent.intervals:
                    interval_stages.append({
                        "name": getattr(interval, 'name', 'work'),
                        "duration_minutes": interval.duration_minutes,
                        "hr_zone": [workout_intent.target_bpm_min, workout_intent.target_bpm_max],
                        "bpm_range": [interval.target_bpm, interval.target_bpm],
                    })
                workout_data["interval_stages"] = interval_stages

            # Add music preferences if provided
            if workout_intent.music_genres:
                workout_data["genres"] = workout_intent.music_genres
            if workout_intent.music_prompt:
                workout_data["prompt"] = workout_intent.music_prompt

            # Insert workout
            result = (
                client.table("workouts")
                .insert(workout_data)
                .execute()
            )

            if result.data and len(result.data) > 0:
                workout_id = result.data[0]["id"]
                logger.info(f"Created workout {workout_id} for user {user_id}")
                return workout_id
            else:
                logger.error("Failed to create workout - no data returned")
                return None

        except Exception as e:
            logger.error(f"Error creating workout in database: {e}")
            return None

    def _format_playlist_message(
        self,
        playlist: PlaylistResponse,
        spotify_info: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Format playlist into user-friendly message.

        Args:
            playlist: Generated playlist response
            spotify_info: Optional Spotify playlist info (id, url)

        Returns:
            Formatted message string
        """
        bpm_progression = f"{playlist.bpm_range[0]}-{playlist.bpm_range[1]} BPM"

        if spotify_info and spotify_info.get("url"):
            message = f"""✓ Плейлист готовий і створено в Spotify!

🎵 **{playlist.total_tracks} треків, {playlist.total_duration_minutes:.1f} хв**
🎚️ BPM: {bpm_progression}

{playlist.curation_notes or ''}

Тисни "Open in Spotify" щоб почати тренування! 🏃‍♂️
"""
        else:
            message = f"""✓ Плейлист готовий!

🎵 **{playlist.total_tracks} треків, {playlist.total_duration_minutes:.1f} хв**
🎚️ BPM: {bpm_progression}

{playlist.curation_notes or ''}

Плейлист згенеровано. Для створення в Spotify потрібна автентифікація.
"""
        return message

    async def _create_spotify_playlist_from_llm(
        self,
        user_id: str,
        playlist: PlaylistResponse,
        workout_intent: WorkoutIntent,
    ) -> Optional[Dict[str, Any]]:
        """
        Create Spotify playlist from LLM-generated playlist.

        Args:
            user_id: User ID
            playlist: LLM-generated playlist
            workout_intent: Workout intent for naming

        Returns:
            Spotify playlist info (id, url) or None if failed
        """
        try:
            # Get user's Spotify token
            client = supabase_service.get_client()
            user_data = (
                client.table("users")
                .select("spotify_access_token, spotify_user_id, spotify_token_expires_at")
                .eq("id", user_id)
                .execute()
            )

            if not user_data.data or not user_data.data[0].get("spotify_access_token"):
                logger.debug(f"User {user_id} not authenticated with Spotify")
                return None

            # Check token expiration
            expires_at_str = user_data.data[0].get("spotify_token_expires_at")
            if expires_at_str:
                from datetime import datetime
                expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
                if expires_at <= datetime.now(expires_at.tzinfo):
                    logger.warning(f"User {user_id} Spotify token expired")
                    return None

            access_token = user_data.data[0]["spotify_access_token"]
            spotify_user_id = user_data.data[0].get("spotify_user_id")

            if not spotify_user_id:
                # Get Spotify user ID from API
                user_client = self.spotify_service.get_user_client(access_token)
                spotify_user = user_client.current_user()
                spotify_user_id = spotify_user.get("id")
                if not spotify_user_id:
                    logger.warning(f"Could not get Spotify user ID for user {user_id}")
                    return None

            # Search for tracks in Spotify
            track_uris = []
            user_client = self.spotify_service.get_user_client(access_token)

            for track in playlist.tracks:
                spotify_track = await self.spotify_service.search_track_by_name(
                    track_name=track.title,
                    artist_name=track.artist,
                    limit=1,
                )
                if spotify_track and spotify_track.get("uri"):
                    track_uris.append(spotify_track["uri"])

            if not track_uris:
                logger.warning("No tracks found in Spotify for LLM playlist")
                return None

            # Create playlist name
            workout_type_map = {
                "continuous": "Стабільна",
                "intervals": "Інтервальна",
                "fartlek": "Фартлек",
                "recovery": "Відновлення",
            }
            workout_name = workout_type_map.get(workout_intent.workout_type, "Тренування")
            playlist_name = f"RunBeat: {workout_name} пробіжка ({int(playlist.total_duration_minutes)} хв)"

            # Create playlist in Spotify
            playlist_info = await self.spotify_service.create_playlist(
                user_client=user_client,
                user_id=spotify_user_id,
                name=playlist_name,
                tracks=track_uris,
                description=playlist.curation_notes or f"AI-згенерований плейлист для {workout_name.lower()} тренування",
            )

            return playlist_info

        except Exception as e:
            logger.error(f"Failed to create Spotify playlist from LLM: {e}")
            return None

    def _create_conversation(self, user_id: str) -> str:
        """
        Create new conversation.

        Args:
            user_id: User identifier

        Returns:
            New conversation ID
        """
        conversation_id = str(uuid4())

        self.conversations[conversation_id] = {
            "id": conversation_id,
            "user_id": user_id,
            "state": ConversationStateEnum.NEW,
            "messages": [],
            "workout_intent": None,
            "playlist": None,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        return conversation_id

    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get conversation by ID.

        Args:
            conversation_id: Conversation identifier

        Returns:
            Conversation data or None
        """
        return self.conversations.get(conversation_id)

    def clear_old_conversations(self, max_age_hours: int = 24):
        """
        Clear conversations older than max_age_hours.

        Args:
            max_age_hours: Maximum age in hours
        """
        cutoff = datetime.utcnow().timestamp() - (max_age_hours * 3600)

        to_delete = []
        for conv_id, conv in self.conversations.items():
            created = datetime.fromisoformat(conv["created_at"]).timestamp()
            if created < cutoff:
                to_delete.append(conv_id)

        for conv_id in to_delete:
            del self.conversations[conv_id]

        if to_delete:
            logger.info(f"Cleared {len(to_delete)} old conversations")

    async def _load_conversation(
        self, conversation_id: str, user_id: str
    ) -> Optional[Dict]:
        """
        Load conversation from database.

        Args:
            conversation_id: Conversation ID
            user_id: User ID (for security)

        Returns:
            Conversation dictionary or None if not found
        """
        try:
            client = supabase_service.get_client()
            response = (
                client.table("conversations")
                .select("*")
                .eq("id", conversation_id)
                .eq("user_id", user_id)
                .execute()
            )

            if response.data and len(response.data) > 0:
                conv_data = response.data[0]
                # Store in memory cache
                self.conversations[conversation_id] = conv_data
                return conv_data
            return None
        except Exception as e:
            logger.error(f"Error loading conversation: {e}")
            return None

    async def _save_conversation(self, conversation: Dict) -> None:
        """
        Save conversation to database.

        Args:
            conversation: Conversation dictionary
        """
        try:
            client = supabase_service.get_client()
            # Upsert conversation
            client.table("conversations").upsert(
                {
                    "id": conversation["id"],
                    "user_id": conversation["user_id"],
                    "state": conversation.get("state", ConversationStateEnum.NEW),
                    "messages": conversation["messages"],
                    "workout_intent": conversation.get("workout_intent"),
                    "playlist": conversation.get("playlist"),
                    "created_at": conversation.get("created_at"),
                    "updated_at": conversation.get("updated_at"),
                }
            ).execute()
            logger.debug(f"Saved conversation {conversation['id']}")
        except Exception as e:
            logger.error(f"Error saving conversation: {e}")
            raise


# Export
__all__ = ["ConversationManager", "ConversationStateEnum", "ConversationAction"]
