"""
==================================================
| Main script for running data-to-paper projects |
==================================================

To run a project, use one of these syntaxes:

1. To interactively choose an existing project or create a new one, simply run:
    `python run.py`

2. To a run a project with one of the example datasets:
    `python run.py <project_name>`
    where <project_name> is one of:
        - default: Hypothesis testing - interactive setup (same as running without a project name)
        - diabetes: Hypothesis testing - diabetes dataset with an open research goal
        - social_network: Hypothesis testing - social network dataset with an open research goal
        - nrp_nicu: Hypothesis testing - NRP NICU dataset with a predefined research goal
        - ML_easy: ML Treatment Optimization dataset with a predefined research goal (easy)
        - ML_medium: ML Treatment Optimization dataset with a predefined research goal (medium)
        - ML_hard: ML Treatment Optimization dataset with a predefined research goal (difficult)
        - toy: Toy example of a simple two-step research process

3. Run a custom project:
    `python run.py --research_type <research_type> --project_folder <project_folder>`

    <research_type>:
    One of:
        - `hypothesis_testing`: Hypothesis testing (default if not provided)
        - `toy_example`: Toy example of a two-step research process
        [Additional research types will be added in the future]

    <project_folder>:
    The path to the project folder (containing the project data-to-paper-xxx.json file).
    The path can be absolute or relative to the `projects` of the repo (e.g., 'diabetes/diabetes_open_goal').
    If not provided, the project folder will be interactively chosen, or interactively created.

In all the above syntaxes, you can also provide a `--run_name` argument to specify the name of a folder,
within `runs` folder of the project folder, where the results will be saved.
Default is run_name is `run_001`.

The script will run the project and save the results in the specified run folder.

See the `env.py` file for setting other available options.
"""

import argparse
import os
import sys

from data_to_paper.base_steps.run_all_steps import set_project_and_run
from data_to_paper.env import BASE_FOLDER
from data_to_paper.research_types.hypothesis_testing.steps_runner import HypothesisTestingStepsRunner
from data_to_paper.research_types.toy_example.steps_runner import ToyStepsRunner

# setup the QT_QPA_PLATFORM environment variable to 'xcb' if the system is Linux
if sys.platform == 'linux':
    os.environ['QT_QPA_PLATFORM'] = 'xcb'

# Currently supported research types:
# We currently only support simple hypothesis-testing research.
# A toy example of a two-step research process is also available
# to demonstrate how new research types can be added.
# We anticipate adding more research types in the future.
RESEARCH_TYPES_TO_STEPS_RUNNERS = {
    'hypothesis_testing': HypothesisTestingStepsRunner,
    'toy_example': ToyStepsRunner,
}

DEFAULT_RUN_NAME = 'run_001'

# Predefined projects:
RUN_PARAMETERS = {
    # Default settings: Hypothesis testing - interactive setup
    'default': [HypothesisTestingStepsRunner, None],

    # Specific demo datasets
    'diabetes': [HypothesisTestingStepsRunner, 'diabetes/open_goal'],
    'nrp_nicu': [HypothesisTestingStepsRunner, 'nrp_nicu/fixed_goal'],
    'ML_hard': [HypothesisTestingStepsRunner, 'ML/fixed_goal_hard'],
    'ML_medium': [HypothesisTestingStepsRunner, 'ML/fixed_goal_medium'],
    'ML_easy': [HypothesisTestingStepsRunner, 'ML/fixed_goal_easy'],
    'social_network': [HypothesisTestingStepsRunner, 'social_network/open_goal'],

    # Toy example of a two-step research process:
    'toy': [ToyStepsRunner, 'toy_example/prime_numbers'],
}


def extract_version_from_toml(file_path: str = None) -> str:
    # Can also use toml.load(file_path), but more dependencies...
    file_path = file_path or BASE_FOLDER / '..' / '..' / 'pyproject.toml'
    with open(file_path, "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith("version"):
                try:
                    return line.split('"')[1]
                except IndexError:
                    pass
    return "unknown"


def run():
    parser = argparse.ArgumentParser()

    parser.add_argument('project', type=str, nargs='?', default=None)
    parser.add_argument('--run_name', type=str, default=None)
    parser.add_argument('--project_folder', type=str, default=None)
    parser.add_argument('--research_type', type=str, default=None)
    parser.add_argument('--version', action='store_true', help="Display the version of the tool")
    args = parser.parse_args()
    if args.version:
        print(f"data-to-paper version {extract_version_from_toml()}")
        return

    project = args.project
    run_name = args.run_name
    project_folder = args.project_folder
    research_type = args.research_type

    run_name = run_name or DEFAULT_RUN_NAME

    if project:
        if project not in RUN_PARAMETERS:
            raise ValueError(f"Project '{project}' is not recognized.\n"
                             f"Please choose one of these pre-set projects {list(RUN_PARAMETERS.keys())}")
        if project_folder is not None:
            raise ValueError("You can't provide a project folder when using a predefined project")
        if research_type is not None:
            raise ValueError("You can't provide a research type when using a predefined project")
        steps_runner_cls, project_folder = RUN_PARAMETERS[project]
    else:
        research_type = research_type or 'hypothesis_testing'
        steps_runner_cls = RESEARCH_TYPES_TO_STEPS_RUNNERS[research_type]

    set_project_and_run(steps_runner_cls, project_directory=project_folder, run_name=run_name)


def main():
    run()


if __name__ == '__main__':
    main()
