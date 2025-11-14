"""
Supervisor (Conversation Orchestrator) using LangChain.
"""
from typing import Optional, Dict, Any, List
from loguru import logger

from app.agents.conversation import ConversationAgent
from app.agents.parser import WorkoutParserAgent
from app.agents.manager import WorkoutManagerAgent
from app.agents.curator import MusicCuratorAgent
from app.schemas.llm_responses import WorkoutIntent, PlaylistResponse


class ConversationOrchestrator:
    """
    Supervisor that orchestrates all agents in the conversation flow.

    Coordinates:
    - ConversationAgent: Natural conversation
    - WorkoutParserAgent: Parse workout intent
    - WorkoutManagerAgent: Create and activate workouts
    - MusicCuratorAgent: Generate playlists
    """

    def __init__(self):
        """Initialize ConversationOrchestrator."""
        self.conversation_agent = ConversationAgent()
        self.parser_agent = WorkoutParserAgent()
        self.manager_agent = WorkoutManagerAgent()
        self.curator_agent = MusicCuratorAgent()

        logger.info("ConversationOrchestrator initialized")

    def _is_explicit_workout_request(self, message: str) -> bool:
        """
        Check if message is an explicit workout request (contains workout keywords).

        Args:
            message: User message

        Returns:
            True if message contains workout-related keywords
        """
        message_lower = message.lower().strip()

        # Workout type keywords
        workout_types = [
            "інтервали", "intervals", "фартлек", "fartlek",
            "стабільна", "steady", "пробіжка", "біг", "run",
            "тренування", "workout", "тренувань", "тренуванням"
        ]

        # Duration keywords
        duration_keywords = [
            "хв", "хвилин", "min", "minutes", "година", "hour",
            "год", "часу", "time"
        ]

        # Intensity keywords
        intensity_keywords = [
            "легк", "easy", "легка", "легкий", "легку",
            "помірн", "moderate", "середн", "medium",
            "темпов", "tempo", "швидк", "fast", "висок", "high",
            "інтенсивн", "intensity"
        ]

        # Music keywords
        music_keywords = [
            "музик", "music", "плейлист", "playlist",
            "жанр", "genre", "рок", "rock", "поп", "pop",
            "електрон", "electronic", "електронік", "edm"
        ]

        # Check if message contains workout-related content
        has_workout_type = any(
            keyword in message_lower for keyword in workout_types)
        has_duration = any(
            keyword in message_lower for keyword in duration_keywords)
        has_intensity = any(
            keyword in message_lower for keyword in intensity_keywords)
        has_music = any(keyword in message_lower for keyword in music_keywords)

        # Consider it explicit if it has workout type + (duration OR intensity OR music)
        # Or if it has duration + intensity
        is_explicit = (
            (has_workout_type and (has_duration or has_intensity or has_music)) or
            (has_duration and has_intensity) or
            (has_duration and has_music)
        )

        return is_explicit

    async def process_message(
        self,
        user_id: str,
        message: str,
        conversation_state: Optional[Dict[str, Any]] = None,
        user_preferences: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Process user message through appropriate agent pipeline.

        Args:
            user_id: User ID
            message: User's message
            conversation_state: Current conversation state
            user_preferences: User preferences

        Returns:
            Response data with state, action, and message
        """
        # Initialize conversation state if not provided
        if not conversation_state:
            conversation_state = {
                "state": "new",
                "workout_intent": None,
                "workout_id": None,
                "messages": [],
            }

        current_state = conversation_state.get("state", "new")
        logger.info(f"Processing message in state: {current_state}")

        # Route to appropriate agent based on state
        if current_state == "new" or current_state == "needs_clarification":
            # Check if message is an explicit workout request (skip ConversationAgent for speed)
            if self._is_explicit_workout_request(message):
                logger.info(
                    "Detected explicit workout request, skipping ConversationAgent")
                # Parse intent directly
                return await self._handle_intent_parsing(
                    user_id=user_id,
                    message=message,
                    conversation_state=conversation_state,
                )

            # Use ConversationAgent to gather information for unclear requests
            return await self._handle_conversation(
                user_id=user_id,
                message=message,
                conversation_state=conversation_state,
                user_preferences=user_preferences,
            )

        elif current_state == "intent_ready":
            # Parse intent and check if complete
            return await self._handle_intent_parsing(
                user_id=user_id,
                message=message,
                conversation_state=conversation_state,
            )

        elif current_state == "workout_confirmation":
            # Handle workout confirmation (Да/Ні)
            return await self._handle_workout_confirmation(
                user_id=user_id,
                message=message,
                conversation_state=conversation_state,
            )

        elif current_state == "workout_created":
            # Workout created, can generate playlist
            return await self._handle_playlist_generation(
                user_id=user_id,
                message=message,
                conversation_state=conversation_state,
                user_preferences=user_preferences,
            )

        else:
            # Unknown state - default to conversation
            logger.warning(
                f"Unknown state: {current_state}, defaulting to conversation")
            return await self._handle_conversation(
                user_id=user_id,
                message=message,
                conversation_state=conversation_state,
                user_preferences=user_preferences,
            )

    async def _handle_conversation(
        self,
        user_id: str,
        message: str,
        conversation_state: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Handle conversation phase - gather information."""
        # Get conversation history
        conversation_history = conversation_state.get("messages", [])

        # Use ConversationAgent to respond
        response = await self.conversation_agent.respond(
            message=message,
            user_id=user_id,
            conversation_history=conversation_history,
            user_preferences=user_preferences,
        )

        # Update conversation state
        conversation_state["messages"].append(
            {"role": "user", "content": message})
        conversation_state["messages"].append(
            {"role": "assistant", "content": response})

        # Try to parse intent from conversation (only if message seems workout-related)
        # Don't try to parse if it's just a confirmation response
        workout_intent = None
        message_lower = message.lower().strip()
        confirmation_responses = ["да", "так",
                                  "ні", "no", "yes", "n", "y", "ок", "ok"]

        # Only try parsing if message is not a simple confirmation
        if not any(response in message_lower for response in confirmation_responses) or len(message_lower) > 3:
            try:
                workout_intent = await self.parser_agent.parse(
                    message=message,
                    conversation_history=conversation_history,
                )
            except Exception as e:
                logger.warning(
                    f"Failed to parse intent in conversation handler: {e}")
                workout_intent = None

        # Check if intent is complete
        if workout_intent and self._is_intent_complete(workout_intent):
            # Intent is complete - ask for confirmation
            conversation_state["workout_intent"] = workout_intent.model_dump()
            conversation_state["state"] = "workout_confirmation"

            workout_summary = self._format_workout_summary(workout_intent)
            confirmation_message = (
                f"Ось що я зрозумів про твоє тренування:\n\n{workout_summary}\n\n"
                "Створити воркаут? (Да/Ні)"
            )

            return {
                "state": "workout_confirmation",
                "action": "ask_confirmation",
                "message_to_user": confirmation_message,
                "workout_intent": workout_intent.model_dump(),
            }
        else:
            # Intent not complete - continue conversation
            conversation_state["state"] = "needs_clarification"
            if workout_intent:
                conversation_state["workout_intent"] = workout_intent.model_dump(
                )

            return {
                "state": "needs_clarification",
                "action": "ask_clarification",
                "message_to_user": response,
                "workout_intent": workout_intent.model_dump() if workout_intent else None,
            }

    async def _handle_intent_parsing(
        self,
        user_id: str,
        message: str,
        conversation_state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Handle intent parsing phase."""
        conversation_history = conversation_state.get("messages", [])

        # Parse intent
        workout_intent = await self.parser_agent.parse(
            message=message,
            conversation_history=conversation_history,
        )

        if workout_intent and self._is_intent_complete(workout_intent):
            conversation_state["workout_intent"] = workout_intent.model_dump()
            conversation_state["state"] = "workout_confirmation"

            workout_summary = self._format_workout_summary(workout_intent)
            confirmation_message = (
                f"Ось що я зрозумів:\n\n{workout_summary}\n\n"
                "Створити воркаут? (Да/Ні)"
            )

            return {
                "state": "workout_confirmation",
                "action": "ask_confirmation",
                "message_to_user": confirmation_message,
                "workout_intent": workout_intent.model_dump(),
            }
        else:
            return {
                "state": "needs_clarification",
                "action": "ask_clarification",
                "message_to_user": "Потрібно більше інформації. Опиши тренування детальніше.",
                "workout_intent": workout_intent.model_dump() if workout_intent else None,
            }

    async def _handle_workout_confirmation(
        self,
        user_id: str,
        message: str,
        conversation_state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Handle workout confirmation (Да/Ні)."""
        message_lower = message.lower().strip()
        positive_responses = ["да", "так", "yes",
                              "y", "ok", "ок", "створ", "створити"]
        negative_responses = ["ні", "no", "n", "не", "не треба", "скасувати"]

        is_positive = any(
            response in message_lower for response in positive_responses)
        is_negative = any(
            response in message_lower for response in negative_responses)

        if not is_positive and not is_negative:
            return {
                "state": "workout_confirmation",
                "action": "ask_confirmation",
                "message_to_user": "Не зовсім зрозумів. Будь ласка, відповідь 'Да' або 'Ні'. Створити воркаут?",
                "workout_intent": conversation_state.get("workout_intent"),
            }

        if is_positive:
            # Create workout
            workout_intent_dict = conversation_state.get("workout_intent")
            if not workout_intent_dict:
                return {
                    "state": "error",
                    "action": "error",
                    "message_to_user": "Вибачте, не вдалось знайти дані про тренування.",
                }

            workout_intent = WorkoutIntent(**workout_intent_dict)

            # Use WorkoutManagerAgent to create and activate workout
            result = await self.manager_agent.create_and_activate_workout(
                user_id=user_id,
                workout_intent=workout_intent,
            )

            # Extract workout ID from result
            if "ID:" in result:
                workout_id = result.split("ID:")[-1].strip()
                conversation_state["workout_id"] = workout_id
                conversation_state["state"] = "workout_created"

                return {
                    "state": "workout_created",
                    "action": "workout_created",
                    "message_to_user": (
                        f"✅ Воркаут успішно створено!\n\n"
                        f"Ти можеш почати тренування або згенерувати плейлист для нього. "
                        f"Якщо будуть якісь побажання - звертайся!"
                    ),
                    "workout_id": workout_id,
                    "workout_intent": workout_intent_dict,
                }
            else:
                return {
                    "state": "error",
                    "action": "error",
                    "message_to_user": f"Вибачте, не вдалось створити воркаут: {result}",
                }
        else:
            # User declined
            conversation_state["state"] = "complete"
            return {
                "state": "complete",
                "action": "declined",
                "message_to_user": (
                    "Зрозуміло! Якщо будуть якісь побажання - звертайся. "
                    "Готовий допомогти з тренуваннями! 💪"
                ),
            }

    async def _handle_playlist_generation(
        self,
        user_id: str,
        message: str,
        conversation_state: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Handle playlist generation after workout is created."""
        workout_intent_dict = conversation_state.get("workout_intent")
        if not workout_intent_dict:
            return {
                "state": "error",
                "action": "error",
                "message_to_user": "Вибачте, не вдалось знайти дані про тренування.",
            }

        workout_intent = WorkoutIntent(**workout_intent_dict)

        # Use MusicCuratorAgent to generate playlist
        playlist = await self.curator_agent.generate_playlist(
            workout_intent=workout_intent,
            user_id=user_id,
            user_preferences=user_preferences,
        )

        conversation_state["playlist"] = playlist.model_dump()
        conversation_state["state"] = "complete"

        return {
            "state": "complete",
            "action": "playlist_generated",
            "message_to_user": f"✅ Плейлист готовий! {playlist.total_tracks} треків, {playlist.total_duration_minutes:.1f} хв",
            "playlist": playlist.model_dump(),
            "workout_id": conversation_state.get("workout_id"),
        }

    def _is_intent_complete(self, intent: WorkoutIntent) -> bool:
        """Check if workout intent is complete."""
        if not intent.workout_type:
            return False
        if not intent.duration_minutes or intent.duration_minutes < 5:
            return False
        if not intent.target_bpm_min or not intent.target_bpm_max:
            return False
        if intent.confidence < 0.6:
            return False
        if intent.workout_type == "intervals" and not intent.intervals:
            return False
        return True

    def _format_workout_summary(self, intent: WorkoutIntent) -> str:
        """Format workout intent into user-friendly summary."""
        workout_type_map = {
            "continuous": "Стабільна пробіжка",
            "intervals": "Інтервальна пробіжка",
            "fartlek": "Фартлек",
            "recovery": "Відновлювальна пробіжка",
        }

        if intent.target_bpm_min < 120:
            intensity_desc = "легка"
        elif intent.target_bpm_min < 150:
            intensity_desc = "помірна"
        else:
            intensity_desc = "висока"

        workout_type = workout_type_map.get(intent.workout_type, "Пробіжка")
        summary = f"🏃 **{workout_type}**\n"
        summary += f"⏱️ Тривалість: {intent.duration_minutes} хвилин\n"
        summary += f"⚡ Інтенсивність: {intensity_desc}\n"
        summary += f"🎵 BPM: {intent.target_bpm_min}-{intent.target_bpm_max}"

        return summary
