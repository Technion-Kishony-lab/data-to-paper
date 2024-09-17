from data_to_paper.base_cast import Agent
from data_to_paper.base_cast.types import Profile

from .env import THEME_NAME

# load theme:
theme = THEME_NAME


class DemoAgent(Agent):
    Performer = 'Performer'
    Director = 'Director'
    Debugger = 'Debugger'
    Writer = 'Writer'

    @classmethod
    def get_primary_agent(cls) -> Agent:
        return cls.Performer

    @classmethod
    def get_human_agent(cls) -> Agent:
        return cls.Director

    def get_conversation_name(self) -> str:
        return AGENTS_TO_CONVERSATION_NAMES[self]

    @property
    def profile(self) -> Profile:
        return getattr(theme, self.name)


assert all(agent.profile.agent_name == agent.name for agent in Agent), \
    f"Agent name in theme {THEME_NAME} does not match Agent enum"


AGENTS_TO_CONVERSATION_NAMES = {
    DemoAgent.Performer: None,
    DemoAgent.Director: 'get data',
    DemoAgent.Debugger: 'debug',
    DemoAgent.Writer: 'write paper',
}
