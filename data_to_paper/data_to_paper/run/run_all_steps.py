import sys

from data_to_paper.base_steps import BaseStepsRunner
from data_to_paper.env import CHOSEN_APP
from data_to_paper.interactive.get_app import get_or_create_app


def run_all_steps(step_runner: BaseStepsRunner):
    if CHOSEN_APP != 'pyside':
        step_runner.run_all_steps()
    else:
        app = get_or_create_app()
        app.start_worker(step_runner.run_all_steps)
        x = app.q_application.exec()
        sys.exit(x)
