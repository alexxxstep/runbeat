"""
This module initializes the agents used in the application.
"""
from .supervisor import supervisor_agent
from .manager import WorkoutManagerAgent
from .curator import MusicCuratorAgent
from .workout_builder_agent import WorkoutBuilderAgent

__all__ = [
    "supervisor_agent",
    "WorkoutManagerAgent",
    "MusicCuratorAgent",
    "WorkoutBuilderAgent",
]
