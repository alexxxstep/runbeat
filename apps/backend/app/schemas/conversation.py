from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from .workout import Workout

# The parameter the assistant is currently asking the user about
CurrentQuestion = Literal[
    "type",
    "duration",
    "intensity",
    "genres",
    "prompt",
    "final_confirmation",
    "none"
]


class ConversationState(BaseModel):
    """Represents the state of a workout creation conversation."""

    user_id: str
    active_workout: Optional[Workout] = None
    collected_parameters: dict = Field(default_factory=dict)

    # Track what the assistant's last question was about
    last_question: CurrentQuestion = "none"

    # A log of the conversation to provide context to the LLM
    history: List[dict] = Field(default_factory=list)

    class Config:
        from_attributes = True


class ConversationUpdate(BaseModel):
    """Represents the output from the Workout Builder Agent."""

    new_state: ConversationState
    response_message: str
