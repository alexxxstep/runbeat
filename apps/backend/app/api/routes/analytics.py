"""
Analytics routes for conversation insights and prompt optimization.
"""
from fastapi import APIRouter, Query
from typing import Dict, Any
from loguru import logger

from app.services.conversation_service import conversation_service

router = APIRouter()


@router.get("/conversation-insights")
async def get_conversation_insights(
    days: int = Query(30, description="Number of days to analyze", ge=1, le=365)
) -> Dict[str, Any]:
    """
    Get insights from conversations for prompt optimization.

    Analyzes:
    - Completion rate
    - Abandonment rate
    - Most common genres
    - Average messages per conversation

    Args:
        days: Number of days to analyze (default: 30)

    Returns:
        Dictionary with insights
    """
    try:
        insights = await conversation_service.get_conversation_insights(days=days)
        logger.info(f"Generated conversation insights for last {days} days")
        return {
            "success": True,
            "insights": insights,
        }

    except Exception as e:
        logger.error(f"Error generating insights: {e}")
        return {
            "success": False,
            "error": str(e),
        }


@router.get("/user-patterns/{user_id}")
async def get_user_patterns(user_id: str) -> Dict[str, Any]:
    """
    Get personalized patterns for a specific user.

    Returns:
    - Favorite genres
    - Typical workout duration
    - Preferred workout type
    - Common intensity

    Args:
        user_id: User ID

    Returns:
        Dictionary with user patterns
    """
    try:
        patterns = await conversation_service.get_user_patterns(user_id)
        return {
            "success": True,
            "user_id": user_id,
            "patterns": patterns,
        }

    except Exception as e:
        logger.error(f"Error fetching user patterns: {e}")
        return {
            "success": False,
            "error": str(e),
        }


@router.get("/recommendations")
async def get_prompt_recommendations(
    days: int = Query(30, description="Number of days to analyze", ge=1, le=365)
) -> Dict[str, Any]:
    """
    Get recommendations for prompt optimization based on conversation analysis.

    Analyzes patterns and suggests improvements to the agent prompt.

    Args:
        days: Number of days to analyze (default: 30)

    Returns:
        Dictionary with recommendations
    """
    try:
        insights = await conversation_service.get_conversation_insights(days=days)

        recommendations = []

        # Analyze completion rate
        completion_rate = insights.get("completion_rate", 0)
        if completion_rate < 70:
            recommendations.append({
                "type": "low_completion_rate",
                "severity": "high",
                "message": f"Completion rate is {completion_rate}%. Consider simplifying the conversation flow or improving error handling.",
            })
        elif completion_rate < 85:
            recommendations.append({
                "type": "moderate_completion_rate",
                "severity": "medium",
                "message": f"Completion rate is {completion_rate}%. Good, but there's room for improvement.",
            })

        # Analyze abandonment rate
        abandonment_rate = insights.get("abandonment_rate", 0)
        if abandonment_rate > 20:
            recommendations.append({
                "type": "high_abandonment",
                "severity": "high",
                "message": f"Abandonment rate is {abandonment_rate}%. Users may be getting confused or frustrated.",
            })

        # Analyze average messages
        avg_messages = insights.get("average_messages_per_conversation", 0)
        if avg_messages > 10:
            recommendations.append({
                "type": "too_many_messages",
                "severity": "medium",
                "message": f"Average {avg_messages} messages per conversation. Consider reducing conversation length.",
            })
        elif avg_messages < 3:
            recommendations.append({
                "type": "too_few_messages",
                "severity": "low",
                "message": f"Average {avg_messages} messages per conversation. Users might be providing all info at once - good!",
            })

        # Analyze most common genres
        common_genres = insights.get("most_common_genres", {})
        if common_genres:
            top_genres = list(common_genres.keys())[:3]
            recommendations.append({
                "type": "popular_genres",
                "severity": "info",
                "message": f"Most popular genres: {', '.join(top_genres)}. Ensure these are well-supported.",
            })

        # Overall health check
        if completion_rate > 85 and abandonment_rate < 15:
            recommendations.append({
                "type": "healthy",
                "severity": "success",
                "message": "Conversation flow is healthy! Keep up the good work.",
            })

        return {
            "success": True,
            "insights": insights,
            "recommendations": recommendations,
            "analyzed_days": days,
        }

    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        return {
            "success": False,
            "error": str(e),
        }

