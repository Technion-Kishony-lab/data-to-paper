from __future__ import annotations

import importlib
from enum import Enum
from typing import Dict, Optional

from scientistgpt.cast.types import Profile, Algorithm
from scientistgpt.env import THEME_NAME

# load theme:
theme = importlib.import_module(f"scientistgpt.cast.themes.{THEME_NAME}")


class Agent(Enum):
    Student = 'Student'
    Mentor = 'Mentor'
    PlanReviewer = 'PlanReviewer'
    Secretary = 'Secretary'
    Debugger = 'Debugger'
    Writer = 'Writer'
    LiteratureReviewer = 'LiteratureReviewer'

    @property
    def profile(self) -> Profile:
        return getattr(theme, self.name)

    @property
    def algorithm(self) -> Algorithm:
        return AGENT_TO_ALGORITHM[self]

    @property
    def system_prompt(self) -> Optional[str]:
        return get_system_prompt(self)

    def pretty_repr(self):
        profile = self.profile
        algorithm_repr = self.algorithm.pretty_repr(self.system_prompt)
        return f"{profile.name} ({profile.title})\n" \
               f"{profile.description}\n" \
               f"{algorithm_repr}"


assert all(agent.profile.agent_name == agent.name for agent in Agent), \
    f"Agent name in theme {THEME_NAME} does not match Agent enum"


AGENT_TO_ALGORITHM: Dict[Agent, Algorithm] = {
    Agent.Student: Algorithm.GTP,
    Agent.Mentor: Algorithm.PRE_PROGRAMMED,
    Agent.PlanReviewer: Algorithm.GTP,
    Agent.Secretary: Algorithm.GTP,
    Agent.Debugger: Algorithm.PRE_PROGRAMMED,
    Agent.Writer: Algorithm.GTP,
    Agent.LiteratureReviewer: Algorithm.GTP,
}


AGENTS_TO_SYSTEM_PROMPTS: Dict[Agent, str] = {}


def _notify_profile_change(agent: Agent):
    """
    hook to update app client of profile change
    """
    pass


def set_system_prompt(agent: Agent, prompt: str):
    AGENTS_TO_SYSTEM_PROMPTS[agent] = prompt
    _notify_profile_change(agent)


def get_system_prompt(agent: Agent) -> Optional[str]:
    return AGENTS_TO_SYSTEM_PROMPTS.get(agent, None)
