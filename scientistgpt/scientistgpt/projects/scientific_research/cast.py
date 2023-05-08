import importlib

from scientistgpt.base_cast import Agent
from scientistgpt.base_cast.types import Profile

from .env import THEME_NAME

# load theme:
theme = importlib.import_module(f'scientistgpt.projects.scientific_research.themes.{THEME_NAME}')

# User-name will be replaced by the name of the user signing in to the app
USER_NAME = 'User'


class ScientificAgent(Agent):
    Performer = 'Performer'
    Director = 'Director'
    GoalReviewer = 'GoalReviewer'
    PlanReviewer = 'PlanReviewer'
    Debugger = 'Debugger'
    InterpretationReviewer = 'InterpretationReviewer'
    Writer = 'Writer'
    CitationExpert = 'CitationExpert'
    TableExpert = 'TableExpert'

    @classmethod
    def get_primary_agent(cls) -> Agent:
        return cls.Performer

    def get_conversation_name(self) -> str:
        return AGENTS_TO_CONVERSATION_NAMES[self]

    @property
    def profile(self) -> Profile:
        return getattr(theme, self.name)

    @property
    def actual_name(self) -> str:
        if self is ScientificAgent.Director:
            return USER_NAME
        return self.profile.name


assert all(agent.profile.agent_name == agent.name for agent in Agent), \
    f"Agent name in theme {THEME_NAME} does not match Agent enum"


AGENTS_TO_CONVERSATION_NAMES = {
    ScientificAgent.Performer: None,
    ScientificAgent.Director: 'get data',
    ScientificAgent.GoalReviewer: 'review goal',
    ScientificAgent.PlanReviewer: 'review plan',
    ScientificAgent.Debugger: 'debug',
    ScientificAgent.InterpretationReviewer: 'results interpretation',
    ScientificAgent.Writer: 'write the paper',
    ScientificAgent.CitationExpert: 'add citations',
    ScientificAgent.TableExpert: 'add tables',
}
