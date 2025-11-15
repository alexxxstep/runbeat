"""Prompts for LangChain agents."""

from app.agents.prompts.parser_prompts import (
    PARSER_AGENT_SYSTEM_PROMPT,
    PARSER_AGENT_USER_PROMPT_TEMPLATE,
)
from app.agents.prompts.curator_prompts import (
    CURATOR_AGENT_SYSTEM_PROMPT,
    CURATOR_AGENT_USER_PROMPT_TEMPLATE,
)
from app.agents.prompts.conversation_prompts import (
    CONVERSATION_AGENT_SYSTEM_PROMPT,
)
from app.agents.prompts.manager_prompts import (
    MANAGER_AGENT_SYSTEM_PROMPT,
    MANAGER_AGENT_USER_PROMPT_TEMPLATE,
)

__all__ = [
    "PARSER_AGENT_SYSTEM_PROMPT",
    "PARSER_AGENT_USER_PROMPT_TEMPLATE",
    "CURATOR_AGENT_SYSTEM_PROMPT",
    "CURATOR_AGENT_USER_PROMPT_TEMPLATE",
    "CONVERSATION_AGENT_SYSTEM_PROMPT",
    "MANAGER_AGENT_SYSTEM_PROMPT",
    "MANAGER_AGENT_USER_PROMPT_TEMPLATE",
]
