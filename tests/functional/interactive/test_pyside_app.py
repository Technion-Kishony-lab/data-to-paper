import sys
import time

import pytest
from PySide6.QtWidgets import QApplication

from data_to_paper.interactive.get_app import get_or_create_q_application_if_app_is_pyside
from data_to_paper.interactive.pyside_app import PysideApp
from data_to_paper.interactive.enum_types import PanelNames


# TODO: Need to make this into a real test
@pytest.mark.skip(reason="Need some work to make it into a real test")
def test_pyside_app():
    def func_to_run():
        # Request text input from the user with an initial text
        text_input = app.request_text(PanelNames.FEEDBACK, 'John', 'write your name:')
        # Simulate a long-running task
        time.sleep(1)
        # Show the processed text in the UI
        app.show_text(PanelNames.SYSTEM_PROMPT, "Hi " + text_input)

    q_application = get_or_create_q_application_if_app_is_pyside()
    app = PysideApp.get_instance()
    app.initialize()
    app.start_worker(func_to_run)
    sys.exit(q_application.exec())
