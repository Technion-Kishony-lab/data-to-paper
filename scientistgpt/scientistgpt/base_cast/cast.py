from __future__ import annotations

from abc import abstractmethod
from enum import Enum
from typing import Dict, Optional

from .types import Profile, Algorithm

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from conversation.actions import Action


class Agent(Enum):

    @property
    @abstractmethod
    def profile(self) -> Profile:
        pass

    @property
    def actual_name(self) -> str:
        return self.profile.name

    @property
    def algorithm(self) -> Algorithm:
        return self.profile.algorithm

    @property
    def system_prompt(self) -> Optional[str]:
        return get_system_prompt(self)

    def pretty_repr(self):
        profile = self.profile
        algorithm_repr = self.algorithm.pretty_repr(self.system_prompt)
        return f"{self.actual_name} ({profile.title})\n" \
               f"{profile.description}\n" \
               f"{algorithm_repr}"


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
