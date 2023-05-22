from unittest import mock

from scientistgpt.base_cast import Agent
from scientistgpt.base_cast.types import Profile


class TestAgent(Agent):
    PERFORMER = 'performer'
    REVIEWER = 'reviewer'

    @classmethod
    def get_primary_agent(cls) -> Agent:
        return cls.PERFORMER

    def get_conversation_name(self) -> str:
        return self.value

    @property
    def profile(self) -> Profile:
        return mock.Mock()
