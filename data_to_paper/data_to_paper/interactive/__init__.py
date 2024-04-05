import sys
from PySide6.QtWidgets import QApplication

from .types import PanelNames
from .base_app import BaseApp

#from .base_app import ConsoleApp as App
from .research_step_window import ResearchStepApp as App

q_application = QApplication(sys.argv)
the_app: BaseApp = App.get_instance()
the_app.initialize()
