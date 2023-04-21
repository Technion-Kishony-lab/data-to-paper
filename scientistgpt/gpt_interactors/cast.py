from enum import Enum
from typing import Dict


class Agent(str, Enum):
    Student = ("Joe", "student, me")
    Mentor = ("Prof. Smith", "my mentor")
    PlanReviewer = ("Prof. Jones", "my research plan reviewer")
    Secretary = ("Mr. Smart", "our department secretary")
    CodeReviewer = ("Dan", "my code-hacker friend")

    def get_name(self):
        return self.value[0]

    def get_description(self):
        return self.value[1]

    def __str__(self):
        return f"{self.get_name()}, {self.get_description()}"


AGENTS_TO_PROFILES: Dict[Agent, str] = {}


def _notify_profile_agent(agent: Agent):
    """
    hook to update app client of profile change
    """
    pass


def set_profile(agent: Agent, profile: str):
    AGENTS_TO_PROFILES[agent] = profile
    _notify_profile_agent(agent)


def get_profile(agent: Agent):
    return AGENTS_TO_PROFILES.get(agent, f'Hello! I am {agent.get_name()}.')
