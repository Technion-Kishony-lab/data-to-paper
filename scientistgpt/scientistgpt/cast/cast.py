from __future__ import annotations

import importlib
from enum import Enum
from typing import Dict, Optional

from scientistgpt.cast.types import Profile, Algorithm
from scientistgpt.env import THEME_NAME

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from scientistgpt.conversation.actions import Action


# load theme:
theme = importlib.import_module(f"scientistgpt.cast.themes.{THEME_NAME}")

# User name will be replaced by the name of the user signing in to the app
USER_NAME = 'User'


class Agent(Enum):
    Student = 'Student'
    Mentor = 'Mentor'
    PlanReviewer = 'PlanReviewer'
    Secretary = 'Secretary'
    Debugger = 'Debugger'
    Writer = 'Writer'
    LiteratureReviewer = 'LiteratureReviewer'
    Director = 'Director'

    @property
    def profile(self) -> Profile:
        return getattr(theme, self.name)

    @property
    def actual_name(self) -> str:
        if self is Agent.Director:
            return USER_NAME
        return self.profile.name

    @property
    def algorithm(self) -> Algorithm:
        return AGENT_TO_ALGORITHM[self]

    @property
    def system_prompt(self) -> Optional[str]:
        return get_system_prompt(self)

    def pretty_repr(self):
        profile = self.profile
        algorithm_repr = self.algorithm.pretty_repr(self.system_prompt)
        return f"{self.actual_name} ({profile.title})\n" \
               f"{profile.description}\n" \
               f"{algorithm_repr}"


assert all(agent.profile.agent_name == agent.name for agent in Agent), \
    f"Agent name in theme {THEME_NAME} does not match Agent enum"


AGENT_TO_ALGORITHM: Dict[Agent, Algorithm] = {
    Agent.Student: Algorithm.GPT,
    Agent.Mentor: Algorithm.PRE_PROGRAMMED,
    Agent.PlanReviewer: Algorithm.GPT,
    Agent.Secretary: Algorithm.GPT,
    Agent.Debugger: Algorithm.PRE_PROGRAMMED,
    Agent.Writer: Algorithm.GPT,
    Agent.LiteratureReviewer: Algorithm.GPT,
}


AGENTS_TO_SYSTEM_PROMPTS: Dict[Agent, str] = {}


def _notify_profile_change(agent: Agent):
    """
    hook to update app client of profile change
    MAOR + ORI
    """
    pass


def set_system_prompt(agent: Agent, prompt: str):
    AGENTS_TO_SYSTEM_PROMPTS[agent] = prompt
    _notify_profile_change(agent)


def get_system_prompt(agent: Agent) -> Optional[str]:
    return AGENTS_TO_SYSTEM_PROMPTS.get(agent, None)


def on_action(action: Action):
    """
    This is called after an action was applied to a conversation.
    """
    from scientistgpt import Role
    from scientistgpt.conversation.actions import AppendMessage
    if isinstance(action, AppendMessage) and action.message.role is Role.SYSTEM:
        set_system_prompt(agent=action.message.agent, prompt=action.message.content)
