"""
Workout Parser Agent using LangChain.
"""
from typing import Optional, List, Dict, Any
import json
import re
from loguru import logger

from langchain.agents import AgentExecutor, create_structured_chat_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.agents.base import BaseAgent
from app.agents.tools.parser_tools import rule_based_parse, validate_intent
from app.agents.prompts.parser_prompts import (
    PARSER_AGENT_SYSTEM_PROMPT,
    PARSER_AGENT_USER_PROMPT_TEMPLATE,
    OUTPUT_PARSER,
)
from app.schemas.llm_responses import WorkoutIntent
from app.services.parsers.rule_based_parser import RuleBasedParser


class WorkoutParserAgent(BaseAgent):
    """
    LangChain-based workout parser agent.

    Uses rule-based parsing first (fast, free), then falls back to AI parsing
    for complex cases.
    """

    def __init__(self):
        """Initialize WorkoutParserAgent."""
        super().__init__(temperature=0.3, max_tokens=500, agent_type="parser")
        self.rule_parser = RuleBasedParser()
        self.output_parser = OUTPUT_PARSER

        # Tools
        self.tools = [
            rule_based_parse,
            validate_intent,
        ]

        # Prompt (must include {tools}, {tool_names}, and {agent_scratchpad})
        # Format the prompt with format_instructions (use replace to avoid formatting {tools} and {tool_names})
        # Escape JSON schema braces in format_instructions to avoid LangChain variable parsing
        format_instructions = OUTPUT_PARSER.get_format_instructions()
        # Escape all braces in format_instructions (they're part of JSON schema, not LangChain variables)
        format_instructions_escaped = format_instructions.replace(
            "{", "{{").replace("}", "}}")

        system_prompt = PARSER_AGENT_SYSTEM_PROMPT.replace(
            "{format_instructions}",
            format_instructions_escaped
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}\n\n{agent_scratchpad}"),
        ])

        # Agent
        self.agent = create_structured_chat_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt,
        )

        # Agent executor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            memory=self.memory,
            verbose=False,
            handle_parsing_errors=True,
            max_iterations=3,
        )

        logger.info("WorkoutParserAgent initialized with LangChain")

    async def process(self, input_data: Dict[str, Any]) -> WorkoutIntent:
        """
        Process workout parsing request.

        Args:
            input_data: Dict with 'message' and optional 'conversation_history'

        Returns:
            WorkoutIntent with parsed parameters
        """
        message = input_data.get("message", "")
        conversation_history = input_data.get("conversation_history", [])

        return await self.parse(message, conversation_history)

    async def parse(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> WorkoutIntent:
        """
        Parse workout intent from message.

        Args:
            message: User's message
            conversation_history: Optional conversation history

        Returns:
            WorkoutIntent with parsed parameters
        """
        # Step 1: Try rule-based parsing first (fast path)
        rule_result = self.rule_parser.parse(message)
        if (
            rule_result
            and rule_result.confidence >= 0.9
            and not rule_result.needs_clarification
        ):
            logger.info(
                f"Using rule-based parsing (confidence: {rule_result.confidence})"
            )
            return rule_result

        # Step 2: Use AI agent for complex cases
        logger.info("Using AI parsing via LangChain agent")

        # Add conversation history to memory if provided
        if conversation_history:
            for msg in conversation_history[:-1]:  # Exclude current message
                role = msg.get("role", "user")
                content = msg.get("content", "")
                self.add_to_memory(role, content)

        # Build user prompt with context
        conversation_context = ""
        if conversation_history:
            context_lines = []
            for msg in conversation_history[-3:]:  # Last 3 messages
                role = msg.get("role", "user")
                content = msg.get("content", "")
                context_lines.append(f"{role.capitalize()}: {content}")
            conversation_context = "\n".join(context_lines)

        user_prompt = PARSER_AGENT_USER_PROMPT_TEMPLATE.format(
            user_message=message,
            conversation_history=conversation_context or "No previous messages",
        )

        try:
            # Invoke agent
            result = await self.agent_executor.ainvoke({
                "input": user_prompt,
            })

            # Extract output
            output_text = result.get("output", "")

            # Parse output
            parsed_intent = self._parse_agent_output(output_text)

            # Add current message to memory
            self.add_to_memory("user", message)
            self.add_to_memory(
                "assistant", f"Parsed: {parsed_intent.workout_type}")

            logger.info(
                f"AI parsing successful: type={parsed_intent.workout_type}, "
                f"duration={parsed_intent.duration_minutes}, "
                f"confidence={parsed_intent.confidence}"
            )

            return parsed_intent

        except Exception as e:
            logger.error(f"Error in AI parsing: {e}")

            # Fallback to rule-based result if available
            if rule_result:
                logger.warning("Using rule-based result as fallback")
                return rule_result

            # Last resort: create minimal intent
            logger.error(
                "Failed to parse workout intent, creating minimal intent")
            return WorkoutIntent(
                workout_type="continuous",
                duration_minutes=30,
                target_bpm_min=120,
                target_bpm_max=140,
                confidence=0.3,
                needs_clarification=True,
                clarification_question="Не зовсім зрозумів. Опиши тренування детальніше.",
            )

    def _parse_agent_output(self, output_text: str) -> WorkoutIntent:
        """
        Parse agent output into WorkoutIntent.

        Args:
            output_text: Agent output text

        Returns:
            WorkoutIntent instance
        """
        # Try to extract JSON from output
        # Agent might return JSON directly or wrapped in text

        # Method 1: Try to parse as direct JSON
        try:
            # Remove markdown code blocks if present
            cleaned = re.sub(r"```json\n?", "", output_text)
            cleaned = re.sub(r"```\n?", "", cleaned)
            cleaned = cleaned.strip()

            # Try parsing as JSON
            json_data = json.loads(cleaned)
            return WorkoutIntent(**json_data)
        except (json.JSONDecodeError, ValueError):
            pass

        # Method 2: Try to find JSON object in text
        json_match = re.search(
            r'\{[^{}]*"workout_type"[^{}]*\}', output_text, re.DOTALL)
        if json_match:
            try:
                json_data = json.loads(json_match.group())
                return WorkoutIntent(**json_data)
            except (json.JSONDecodeError, ValueError):
                pass

        # Method 3: Use output parser
        try:
            return self.output_parser.parse(output_text)
        except Exception:
            pass

        # If all methods fail, raise error
        raise ValueError(f"Failed to parse agent output: {output_text}")
