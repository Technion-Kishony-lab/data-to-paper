from __future__ import annotations
import sys
from typing import Optional

from PySide6.QtWidgets import QApplication

from data_to_paper.env import CHOSEN_APP
from .base_app import BaseApp

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from data_to_paper.base_steps import BaseStepsRunner

IS_APP_INITIALIZED = False
THE_APP: Optional[BaseApp] = None


def get_app() -> Optional[BaseApp]:
    global THE_APP, IS_APP_INITIALIZED
    if not IS_APP_INITIALIZED:
        raise ValueError("App is not initialized")
    return THE_APP


def create_app(q_application: Optional[QApplication] = None, step_runner: BaseStepsRunner = None) \
        -> Optional[BaseApp]:
    global IS_APP_INITIALIZED, THE_APP
    if IS_APP_INITIALIZED:
        raise ValueError("App is already initialized")

    IS_APP_INITIALIZED = True

    if CHOSEN_APP == None:  # noqa  (Mutable)
        THE_APP = None
        return THE_APP
    if CHOSEN_APP == 'pyside':
        from .pyside_app import PysideApp
        if not q_application:
            q_application = QApplication(sys.argv)  # Create QApplication only if not provided
        THE_APP = PysideApp.get_instance()
        THE_APP.q_application = q_application
    elif CHOSEN_APP == 'console':
        from .base_app import ConsoleApp
        THE_APP = ConsoleApp.get_instance()
    else:
        raise ValueError(f"Unknown app type: {CHOSEN_APP}")
    THE_APP.step_runner = step_runner
    return THE_APP
