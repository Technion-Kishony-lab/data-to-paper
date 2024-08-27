import sys
from typing import Type, Optional, Union

from pathlib import Path

from data_to_paper.base_steps import BaseStepsRunner
from data_to_paper.env import CHOSEN_APP
from data_to_paper.interactive.base_app_startup import interactively_create_project_folder, BASE_PROJECT_DIRECTORY
from data_to_paper.interactive.get_app import create_app


def run_all_steps(step_runner: BaseStepsRunner):
    app = create_app(step_runner=step_runner)
    if app is None:
        step_runner.run_all_steps()
    else:
        step_runner.app = app
        exit_code = app.initialize()
        sys.exit(exit_code)


def set_project_and_run(steps_runner_cls: Type[BaseStepsRunner],
                        project_directory: Optional[Union[Path, str]] = None,
                        run_name: str = 'run_001'):
    if isinstance(project_directory, str):
        project_directory = Path(project_directory)
    if project_directory is not None and not project_directory.is_absolute():
        project_directory = BASE_PROJECT_DIRECTORY / project_directory
    if CHOSEN_APP == 'pyside':
        project_directory, config = interactively_create_project_folder(steps_runner_cls, project_directory)
        if project_directory is None:
            return
    else:
        if project_directory is None:
            raise ValueError("You must provide a project directory when not using the interactive app")
    if isinstance(run_name, str):
        output_directory = project_directory / 'runs' / run_name
    else:
        output_directory = run_name
    step_runner = steps_runner_cls(
        project_directory=project_directory,
        output_directory=output_directory,
    )
    run_all_steps(step_runner=step_runner)
