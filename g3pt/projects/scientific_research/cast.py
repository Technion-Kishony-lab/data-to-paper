import importlib

from g3pt.base_cast import Agent
from g3pt.base_cast.types import Profile
from g3pt.projects.scientific_research.env import THEME_NAME

# load theme:
theme = importlib.import_module(f"g3pt.cast.themes.{THEME_NAME}")

# User-name will be replaced by the name of the user signing in to the app
USER_NAME = 'User'


class ScientificAgent(Agent):
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
        if self is ScientificAgent.Director:
            return USER_NAME
        return self.profile.name


assert all(agent.profile.agent_name == agent.name for agent in Agent), \
    f"Agent name in theme {THEME_NAME} does not match Agent enum"
