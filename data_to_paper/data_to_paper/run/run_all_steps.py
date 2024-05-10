import sys

from data_to_paper.base_steps import BaseStepsRunner
from data_to_paper.interactive.get_app import create_app


def run_all_steps(step_runner: BaseStepsRunner, q_application=None):
    app = create_app(q_application=q_application, step_runner=step_runner)
    if app is None:
        step_runner.run_all_steps()
    else:
        step_runner.app = app
        exit_code = app.initialize()
        sys.exit(exit_code)
