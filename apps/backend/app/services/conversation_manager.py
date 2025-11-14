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


class ConversationStateEnum(str, Enum):
    """States in conversation flow."""

    NEW = "new"
    PARSING_INTENT = "parsing_intent"
    NEEDS_CLARIFICATION = "needs_clarification"
    READY_TO_GENERATE = "ready_to_generate"
    GENERATING_PLAYLIST = "generating_playlist"
    COMPLETE = "complete"
    ERROR = "error"


class ConversationAction(str, Enum):
    """Actions conversation manager can take."""

    PARSE_INTENT = "parse_intent"
    ASK_CLARIFICATION = "ask_clarification"
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
    ):
        """
        Initialize conversation manager.

        Args:
            llm_service: LLM service for parsing and generation (creates new if not provided)
            spotify_service: Spotify service for creating playlists (creates new if not provided)
        """
        self.llm_service = llm_service or LLMService()
        self.spotify_service = spotify_service or SpotifyService()
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

            # Build ConversationState
            conversation_state = ConversationState(
                messages=llm_history,
                current_intent=None,
                clarification_needed=False,
            )

            intent = await self.llm_service.parse_workout(
                user_message=message,
                user_context=user_context,
                conversation_state=conversation_state,
            )

            return intent

        except Exception as e:
            logger.error(f"Failed to parse intent: {e}")
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
        if workout_intent.needs_clarification:
            return ConversationAction.ASK_CLARIFICATION, {
                "state": ConversationStateEnum.NEEDS_CLARIFICATION,
                "action": ConversationAction.ASK_CLARIFICATION,
                "message_to_user": workout_intent.clarification_question
                or "Можете уточнити деталі тренування?",
                "workout_intent": workout_intent.model_dump(),
                "confidence": workout_intent.confidence,
            }

        # Check if intent is complete enough to generate playlist
        if self._is_intent_complete(workout_intent):
            # Ready to generate playlist
            logger.info("Intent complete, generating playlist...")

            try:
                playlist = await self.llm_service.generate_playlist(
                    workout_intent=workout_intent,
                    user_preferences=user_preferences,
                )

                # Try to create playlist in Spotify if user is authenticated
                playlist_dict = playlist.model_dump()
                spotify_playlist_info = None

                if conversation.get("user_id"):
                    try:
                        spotify_playlist_info = await self._create_spotify_playlist_from_llm(
                            user_id=conversation["user_id"],
                            playlist=playlist,
                            workout_intent=workout_intent,
                        )
                        if spotify_playlist_info:
                            # Add Spotify info to playlist dict
                            playlist_dict["spotify_playlist_id"] = spotify_playlist_info.get("id")
                            playlist_dict["spotify_url"] = spotify_playlist_info.get("url")
                            logger.info(f"Created Spotify playlist: {spotify_playlist_info.get('url')}")
                    except Exception as spotify_error:
                        logger.warning(f"Failed to create Spotify playlist: {spotify_error}")
                        # Continue without Spotify playlist - LLM playlist is still available

                return ConversationAction.SHOW_PLAYLIST, {
                    "state": ConversationStateEnum.COMPLETE,
                    "action": ConversationAction.SHOW_PLAYLIST,
                    "workout_intent": workout_intent.model_dump(),
                    "playlist": playlist_dict,
                    "message_to_user": self._format_playlist_message(playlist, spotify_playlist_info),
                }

            except Exception as e:
                logger.error(f"Failed to generate playlist: {e}")
                return ConversationAction.ERROR_RESPONSE, {
                    "state": ConversationStateEnum.ERROR,
                    "action": ConversationAction.ERROR_RESPONSE,
                    "message_to_user": "Не вдалось згенерувати плейлист. Спробуй ще раз.",
                    "error": str(e),
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

        # Confidence threshold
        if intent.confidence < 0.7:
            logger.debug(f"Intent confidence too low: {intent.confidence}")
            return False

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
