import sys
import time

from data_to_paper.interactive import q_application, the_app
from data_to_paper.interactive.types import PanelNames


def my_func():
    # Request text input from the user with an initial text
    text_input = the_app.request_text(PanelNames.FEEDBACK, 'John', 'write your name:')
    # Simulate a long-running task
    time.sleep(3)
    # Show the processed text in the UI
    the_app.show_text(PanelNames.SYSTEM_PROMPT, "Hello " + text_input)


# Running the application
the_app.start_worker(my_func)
sys.exit(q_application.exec())
