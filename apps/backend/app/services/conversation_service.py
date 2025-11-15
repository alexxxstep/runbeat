"""
Service for managing conversations in the database.
Provides conversation history, user patterns, and learning capabilities.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from loguru import logger
from collections import Counter

from app.services.supabase_service import supabase_service
from app.schemas.conversation import ConversationState


class ConversationService:
    """Service for managing conversation history and user patterns."""

    def __init__(self):
        """Initialize conversation service."""
        self.client = supabase_service.get_client()

    async def save_conversation(
        self,
        user_id: str,
        state: ConversationState,
        conversation_state: str = "active",
    ) -> Optional[str]:
        """
        Save or update conversation in the database.

        Args:
            user_id: User ID
            state: Current conversation state
            conversation_state: State (active, completed, abandoned)

        Returns:
            Conversation ID if successful, None otherwise
        """
        try:
            # Check if there's an active conversation for this user
            existing = (
                self.client.table("conversations")
                .select("id")
                .eq("user_id", user_id)
                .eq("state", "active")
                .order("updated_at", desc=True)
                .limit(1)
                .execute()
            )

            conversation_data = {
                "user_id": user_id,
                "state": conversation_state,
                "messages": state.history,
                "updated_at": datetime.utcnow().isoformat(),
            }

            # Add collected parameters if available
            if state.collected_parameters:
                conversation_data["workout_intent"] = state.collected_parameters

            if existing.data and len(existing.data) > 0:
                # Update existing conversation
                conversation_id = existing.data[0]["id"]
                result = (
                    self.client.table("conversations")
                    .update(conversation_data)
                    .eq("id", conversation_id)
                    .execute()
                )
                logger.debug(
                    f"Updated conversation {conversation_id} for user {user_id}"
                )
                return conversation_id
            else:
                # Create new conversation
                conversation_data["created_at"] = datetime.utcnow().isoformat()
                result = (
                    self.client.table("conversations")
                    .insert(conversation_data)
                    .execute()
                )
                if result.data and len(result.data) > 0:
                    conversation_id = result.data[0]["id"]
                    logger.info(
                        f"Created new conversation {conversation_id} "
                        f"for user {user_id}"
                    )
                    return conversation_id

            return None

        except Exception as e:
            logger.error(f"Error saving conversation: {e}")
            return None

    async def get_user_conversations(
        self, user_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get recent conversations for a user.

        Args:
            user_id: User ID
            limit: Maximum number of conversations to return

        Returns:
            List of conversations (most recent first)
        """
        try:
            result = (
                self.client.table("conversations")
                .select("*")
                .eq("user_id", user_id)
                .order("updated_at", desc=True)
                .limit(limit)
                .execute()
            )

            return result.data if result.data else []

        except Exception as e:
            logger.error(f"Error fetching user conversations: {e}")
            return []

    async def get_user_patterns(self, user_id: str) -> Dict[str, Any]:
        """
        Analyze user's conversation patterns to provide personalization.

        Analyzes:
        - Favorite music genres
        - Typical workout duration
        - Preferred workout type
        - Common intensity

        Args:
            user_id: User ID

        Returns:
            Dictionary with user patterns
        """
        try:
            # Get last 20 completed conversations (with workout_intent)
            conversations = (
                self.client.table("conversations")
                .select("workout_intent, messages, state")
                .eq("user_id", user_id)
                .in_("state", ["completed", "active"])
                .order("updated_at", desc=True)
                .limit(20)
                .execute()
            )

            if not conversations.data or len(conversations.data) == 0:
                return {
                    "has_history": False,
                    "total_conversations": 0,
                }

            # Extract parameters from conversations
            all_genres = []
            all_durations = []
            all_types = []
            all_intensities = []

            for conv in conversations.data:
                workout_intent = conv.get("workout_intent", {})
                if not workout_intent:
                    continue

                # Collect genres
                genres = workout_intent.get("genres", [])
                if isinstance(genres, list):
                    all_genres.extend(genres)

                # Collect duration
                duration = workout_intent.get("duration_minutes")
                if duration:
                    all_durations.append(duration)

                # Collect type
                workout_type = workout_intent.get("type")
                if workout_type:
                    all_types.append(workout_type)

                # Collect intensity
                intensity = workout_intent.get("intensity")
                if intensity:
                    all_intensities.append(intensity)

            # Calculate patterns
            patterns = {
                "has_history": True,
                "total_conversations": len(conversations.data),
            }

            # Favorite genres (top 3)
            if all_genres:
                genre_counts = Counter(all_genres)
                patterns["favorite_genres"] = [
                    genre for genre, _ in genre_counts.most_common(3)
                ]

            # Average duration
            if all_durations:
                patterns["typical_duration"] = int(sum(all_durations) / len(all_durations))

            # Preferred workout type
            if all_types:
                type_counts = Counter(all_types)
                patterns["preferred_type"] = type_counts.most_common(1)[0][0]

            # Common intensity
            if all_intensities:
                intensity_counts = Counter(all_intensities)
                patterns["common_intensity"] = intensity_counts.most_common(1)[0][0]

            logger.debug(f"Analyzed patterns for user {user_id}: {patterns}")
            return patterns

        except Exception as e:
            logger.error(f"Error analyzing user patterns: {e}")
            return {
                "has_history": False,
                "total_conversations": 0,
            }

    async def mark_conversation_completed(self, user_id: str) -> None:
        """
        Mark the current active conversation as completed.

        Args:
            user_id: User ID
        """
        try:
            result = (
                self.client.table("conversations")
                .update({"state": "completed", "updated_at": datetime.utcnow().isoformat()})
                .eq("user_id", user_id)
                .eq("state", "active")
                .execute()
            )
            logger.debug(f"Marked conversation as completed for user {user_id}")

        except Exception as e:
            logger.error(f"Error marking conversation as completed: {e}")

    async def get_conversation_insights(
        self, days: int = 30
    ) -> Dict[str, Any]:
        """
        Get insights from all conversations for prompt optimization.

        Analyzes:
        - Most common genres that AI fails to recognize
        - Common questions that lead to confusion
        - Successful patterns

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary with insights
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # Get all recent conversations
            conversations = (
                self.client.table("conversations")
                .select("*")
                .gte("updated_at", cutoff_date.isoformat())
                .order("updated_at", desc=True)
                .limit(1000)
                .execute()
            )

            if not conversations.data or len(conversations.data) == 0:
                return {
                    "total_analyzed": 0,
                    "insights": "Not enough data for analysis",
                }

            # Analyze conversations
            total = len(conversations.data)
            completed = sum(
                1 for c in conversations.data if c.get("state") == "completed"
            )
            abandoned = sum(
                1 for c in conversations.data
                if c.get("state") in ["abandoned", "active"] and len(c.get("messages", [])) > 3
            )

            # Extract genres from all conversations
            all_genres = []
            for conv in conversations.data:
                workout_intent = conv.get("workout_intent", {})
                genres = workout_intent.get("genres", [])
                if isinstance(genres, list):
                    all_genres.extend(genres)

            genre_counts = Counter(all_genres)

            insights = {
                "total_analyzed": total,
                "completion_rate": round(completed / total * 100, 2) if total > 0 else 0,
                "abandonment_rate": round(abandoned / total * 100, 2) if total > 0 else 0,
                "most_common_genres": dict(genre_counts.most_common(10)),
                "average_messages_per_conversation": round(
                    sum(len(c.get("messages", [])) for c in conversations.data) / total, 2
                ) if total > 0 else 0,
            }

            logger.info(f"Generated insights from {total} conversations: {insights}")
            return insights

        except Exception as e:
            logger.error(f"Error generating conversation insights: {e}")
            return {
                "total_analyzed": 0,
                "error": str(e),
            }


# Singleton instance
conversation_service = ConversationService()

