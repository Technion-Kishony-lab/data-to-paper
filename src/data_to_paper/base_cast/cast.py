from __future__ import annotations

from abc import abstractmethod
from enum import Enum
from typing import Dict, Optional

from data_to_paper.env import HUMAN_NAME

from .types import Profile, Algorithm

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from data_to_paper.conversation.conversation_actions import Action


class Agent(Enum):

    @classmethod
    @abstractmethod
    def get_primary_agent(cls) -> Agent:
        pass

    @classmethod
    @abstractmethod
    def get_human_agent(cls) -> Agent:
        pass

    @abstractmethod
    def get_conversation_name(self) -> str:
        pass

    @property
    @abstractmethod
    def profile(self) -> Profile:
        pass

    @property
    def skin_name(self) -> str:
        if self is self.get_human_agent():
            return HUMAN_NAME
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
        return f"{self.skin_name} ({profile.title})\n" \
               f"{profile.description}\n" \
               f"{algorithm_repr}"

    def pretty_name(self):
        return f"{self.profile.name} ({self.value})"


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
    from data_to_paper import Role
    from data_to_paper.conversation.conversation_actions import AppendMessage
    if isinstance(action, AppendMessage) and action.message.role is Role.SYSTEM:
        set_system_prompt(agent=action.message.agent, prompt=action.message.content)
