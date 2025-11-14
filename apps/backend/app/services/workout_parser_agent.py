"""
Workout Parser Agent - Hybrid parser combining rule-based and AI parsing.

Uses rule-based parsing for simple cases (fast, free) and falls back to
AI parsing for complex cases.
"""
from typing import Optional, List, Dict
from loguru import logger

from app.schemas.llm_responses import WorkoutIntent
from app.services.llm_service import LLMService
from app.services.parsers.rule_based_parser import RuleBasedParser
from app.services.prompts.prompt_builder import ConversationState, UserContext


class WorkoutParserAgent:
    """
    Hybrid parser agent for workout intent extraction.

    Strategy:
    1. Try rule-based parsing first (fast, free)
    2. If rule-based fails or confidence is low, use AI parsing
    3. Merge results if both succeed (rule-based can enrich AI results)
    """

    def __init__(self, llm_service: LLMService):
        """
        Initialize parser agent.

        Args:
            llm_service: LLM service for AI parsing
        """
        self.llm_service = llm_service
        self.rule_parser = RuleBasedParser()
        logger.info("WorkoutParserAgent initialized")

    async def parse(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        user_context: Optional[UserContext] = None,
    ) -> WorkoutIntent:
        """
        Parse workout intent from message using hybrid approach.

        Args:
            message: User's message
            conversation_history: Optional conversation history
            user_context: Optional user context

        Returns:
            WorkoutIntent with parsed parameters
        """
        # Step 1: Try rule-based parsing first
        rule_result = self.rule_parser.parse(message)

        if rule_result and rule_result.confidence >= 0.9 and not rule_result.needs_clarification:
            logger.info(f"Using rule-based parsing result (confidence: {rule_result.confidence})")
            return rule_result

        # Step 2: Use AI parsing (either rule-based failed or needs clarification)
        logger.info("Falling back to AI parsing")

        # Build conversation state if history provided
        conversation_state = None
        if conversation_history:
            llm_history = [
                {"role": msg.get("role", "user"), "content": msg.get("content", "")}
                for msg in conversation_history[:-1]  # Exclude current message
            ]
            conversation_state = ConversationState(
                messages=llm_history,
                current_intent=None,
                clarification_needed=False,
            )

        # Use AI parsing
        ai_result = await self.llm_service.parse_workout(
            user_message=message,
            user_context=user_context,
            conversation_state=conversation_state,
        )

        # Step 3: Merge results if rule-based found something useful
        if rule_result and rule_result.confidence >= 0.7:
            # Rule-based found partial info - merge with AI result
            merged_result = self._merge_results(rule_result, ai_result)
            logger.info(
                f"Merged rule-based and AI results: "
                f"confidence={merged_result.confidence}"
            )
            return merged_result

        # Return AI result
        return ai_result

    def _merge_results(
        self,
        rule_result: WorkoutIntent,
        ai_result: WorkoutIntent,
    ) -> WorkoutIntent:
        """
        Merge rule-based and AI parsing results.

        Rule-based results take precedence for fields where they have high confidence.
        AI results fill in missing information.

        Args:
            rule_result: Result from rule-based parser
            ai_result: Result from AI parser

        Returns:
            Merged WorkoutIntent
        """
        # Use rule-based values if they are more specific
        # Otherwise use AI values

        # Duration: prefer rule-based if it's more specific
        duration = rule_result.duration_minutes if rule_result.duration_minutes >= 5 else ai_result.duration_minutes

        # BPM: prefer rule-based if it's more specific
        if rule_result.target_bpm_min and rule_result.target_bpm_max:
            bpm_min = rule_result.target_bpm_min
            bpm_max = rule_result.target_bpm_max
        else:
            bpm_min = ai_result.target_bpm_min
            bpm_max = ai_result.target_bpm_max

        # Workout type: prefer rule-based if found
        workout_type = rule_result.workout_type if rule_result.workout_type != 'continuous' else ai_result.workout_type

        # Music preferences: merge both
        music_genres = rule_result.music_genres or ai_result.music_genres
        if rule_result.music_genres and ai_result.music_genres:
            # Combine unique genres
            combined = list(set((rule_result.music_genres or []) + (ai_result.music_genres or [])))
            music_genres = combined if combined else None

        music_prompt = rule_result.music_prompt or ai_result.music_prompt

        # Intervals: prefer AI (rule-based doesn't parse intervals well)
        intervals = ai_result.intervals or rule_result.intervals

        # Confidence: average of both, but cap at 0.95
        confidence = min((rule_result.confidence + ai_result.confidence) / 2, 0.95)

        # Needs clarification: if either needs it, we need it
        needs_clarification = rule_result.needs_clarification or ai_result.needs_clarification
        clarification_question = rule_result.clarification_question or ai_result.clarification_question

        return WorkoutIntent(
            workout_type=workout_type,
            duration_minutes=duration,
            target_bpm_min=bpm_min,
            target_bpm_max=bpm_max,
            intervals=intervals,
            energy_profile=ai_result.energy_profile,  # AI is better at this
            mood=ai_result.mood,  # AI is better at this
            music_genres=music_genres,
            music_prompt=music_prompt,
            confidence=confidence,
            needs_clarification=needs_clarification,
            clarification_question=clarification_question,
        )

