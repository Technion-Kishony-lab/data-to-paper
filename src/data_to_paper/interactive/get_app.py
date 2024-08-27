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
Q_APPLICATION: Optional[QApplication] = None


def get_or_create_q_application_if_app_is_pyside() -> Optional[QApplication]:
    if CHOSEN_APP != 'pyside':
        return None
    global Q_APPLICATION
    if Q_APPLICATION is None:
        Q_APPLICATION = QApplication(sys.argv)
    return Q_APPLICATION


def get_app() -> Optional[BaseApp]:
    global THE_APP, IS_APP_INITIALIZED
    if not IS_APP_INITIALIZED and THE_APP is not None:
        raise ValueError("App is not initialized")
    return THE_APP


def create_app(step_runner: BaseStepsRunner = None) -> Optional[BaseApp]:
    global IS_APP_INITIALIZED, THE_APP
    if IS_APP_INITIALIZED:
        raise ValueError("App is already initialized")

    IS_APP_INITIALIZED = True

    if CHOSEN_APP == None:  # noqa  (Mutable)
        THE_APP = None
        return THE_APP
    if CHOSEN_APP == 'pyside':
        from .pyside_app import PysideApp
        get_or_create_q_application_if_app_is_pyside()
        THE_APP = PysideApp.get_instance()
    elif CHOSEN_APP == 'console':
        from .base_app import ConsoleApp
        THE_APP = ConsoleApp.get_instance()
    else:
        raise ValueError(f"Unknown app type: {CHOSEN_APP}")
    THE_APP.step_runner = step_runner
    return THE_APP
