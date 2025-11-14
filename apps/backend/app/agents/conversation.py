"""
Conversation Agent using LangChain.
"""
from typing import Optional, List, Dict, Any
from loguru import logger

from langchain.agents import AgentExecutor, create_structured_chat_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.agents.base import BaseAgent
from app.agents.tools.database_tools import (
    get_user_preferences,
    get_conversation_history,
    save_conversation,
)
from app.agents.prompts.conversation_prompts import (
    CONVERSATION_AGENT_SYSTEM_PROMPT,
    CONVERSATION_AGENT_USER_PROMPT_TEMPLATE,
)


class ConversationAgent(BaseAgent):
    """
    LangChain-based conversation agent.

    Handles natural conversation with users, asks clarifying questions,
    and gathers workout information.
    """

    def __init__(self):
        """Initialize ConversationAgent."""
        super().__init__(temperature=0.7, max_tokens=300)  # Friendly and conversational
        self.output_parser = None  # Returns natural language, not structured

        # Tools
        self.tools = [
            get_user_preferences,
            get_conversation_history,
            save_conversation,
        ]

        # Prompt (must include {tools}, {tool_names}, and {agent_scratchpad})
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", CONVERSATION_AGENT_SYSTEM_PROMPT),
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

        logger.info("ConversationAgent initialized with LangChain")

    async def process(self, input_data: Dict[str, Any]) -> str:
        """
        Process conversation request.

        Args:
            input_data: Dict with 'message', 'user_id', optional 'conversation_history', 'user_preferences'

        Returns:
            Natural language response string
        """
        message = input_data.get("message", "")
        user_id = input_data.get("user_id")
        conversation_history = input_data.get("conversation_history", [])
        user_preferences = input_data.get("user_preferences")

        return await self.respond(
            message=message,
            user_id=user_id,
            conversation_history=conversation_history,
            user_preferences=user_preferences,
        )

    async def respond(
        self,
        message: str,
        user_id: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        user_preferences: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate conversational response.

        Args:
            message: User's message
            user_id: Optional user ID for preferences
            conversation_history: Optional conversation history
            user_preferences: Optional user preferences dict

        Returns:
            Natural language response string
        """
        logger.info(f"ConversationAgent responding to: {message[:50]}...")

        # Build user prompt with context
        user_prompt = message

        if user_id:
            user_prompt += f"\n\nUser ID: {user_id}. Use get_user_preferences tool if needed."

        if user_preferences:
            prefs_str = ", ".join([
                f"genres: {user_preferences.get('top_genres', [])}",
                f"artists: {user_preferences.get('top_artists', [])}",
            ])
            user_prompt += f"\n\nUser preferences: {prefs_str}"

        # Clear memory first to avoid duplicates
        self.clear_memory()

        # Add conversation history to memory if provided (excluding current message)
        if conversation_history:
            for msg in conversation_history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if content:  # Only add non-empty messages
                    self.add_to_memory(role, content)

        # Add current user message to memory (AgentExecutor will add response automatically)
        self.add_to_memory("user", message)

        try:
            # Invoke agent (memory is automatically used by AgentExecutor)
            result = await self.agent_executor.ainvoke({
                "input": user_prompt,
            })

            # Extract output
            response = result.get("output", "")

            # Note: Memory is already updated by agent_executor, no need to add again

            logger.info(f"ConversationAgent response: {response[:50]}...")
            return response

        except Exception as e:
            logger.error(f"Error in ConversationAgent: {e}")
            # Fallback response
            return "Вибачте, виникла помилка. Спробуйте ще раз або опишіть тренування детальніше."

