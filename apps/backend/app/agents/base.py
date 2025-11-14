"""
Base classes for LangChain agents.
"""
from typing import Optional, List, Dict, Any
from abc import ABC, abstractmethod
from loguru import logger

from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from app.core.config import settings


class BaseAgent(ABC):
    """Base class for all LangChain agents."""

    def __init__(
        self,
        model_name: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 1000,
        agent_type: Optional[str] = None,  # "parser", "curator", "conversation", "supervisor"
    ):
        """
        Initialize base agent.

        Args:
            model_name: OpenAI model name (defaults to settings.OPENAI_MODEL or agent-specific model)
            temperature: LLM temperature
            max_tokens: Maximum tokens in response
            agent_type: Type of agent for model selection ("parser", "curator", "conversation", "supervisor")
        """
        # Select model based on agent type if model_name not provided
        if not model_name and agent_type:
            model_map = {
                "parser": settings.OPENAI_MODEL_PARSER,
                "curator": settings.OPENAI_MODEL_CURATOR,
                "conversation": settings.OPENAI_MODEL_CONVERSATION,
                "supervisor": settings.OPENAI_MODEL_SUPERVISOR,
            }
            model_name = model_map.get(agent_type) or settings.OPENAI_MODEL
        else:
            model_name = model_name or settings.OPENAI_MODEL

        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            api_key=settings.OPENAI_API_KEY,
            max_tokens=max_tokens,
        )
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            max_token_limit=4000,
        )
        logger.info(f"{self.__class__.__name__} initialized with model: {model_name}")

    @abstractmethod
    async def process(self, input_data: Any) -> Any:
        """
        Process input data.

        Args:
            input_data: Input data (type depends on agent)

        Returns:
            Processed output (type depends on agent)
        """
        pass

    def clear_memory(self):
        """Clear agent memory."""
        self.memory.clear()
        logger.debug(f"{self.__class__.__name__} memory cleared")

    def add_to_memory(self, role: str, content: str):
        """
        Add message to memory.

        Args:
            role: Message role ("user" or "assistant")
            content: Message content
        """
        if role == "user":
            self.memory.chat_memory.add_user_message(content)
        elif role == "assistant":
            self.memory.chat_memory.add_ai_message(content)

