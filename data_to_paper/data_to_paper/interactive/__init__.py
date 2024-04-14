import sys
from PySide6.QtWidgets import QApplication

from data_to_paper.env import CHOSEN_APP

from .types import PanelNames
from .human_actions import HumanAction, ButtonClickedHumanAction, TextSentHumanAction
from .base_app import BaseApp

#from .base_app import ConsoleApp as App
if CHOSEN_APP == 'pyside':
    from .research_step_window import ResearchStepApp as App
elif CHOSEN_APP == 'console':
    from .base_app import ConsoleApp as App
elif CHOSEN_APP == None:
    from .base_app import BaseApp as App
else:
    raise ValueError(f"Unknown app type: {CHOSEN_APP}")


q_application = QApplication(sys.argv)
the_app: BaseApp = App.get_instance()
the_app.initialize()
