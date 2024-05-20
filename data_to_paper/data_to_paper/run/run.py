# ============================================== #
# Main script for running data-to-paper projects #
# ============================================== #

from data_to_paper.research_types.hypothesis_testing.steps_runner import HypothesisTestingStepsRunner
from data_to_paper.research_types.toy_example.steps_runner import ToyStepsRunner
from data_to_paper.run.run_all_steps import set_project_and_run

# To run a project, set the following variables:

"""
(1) Research type to run.
    We currently implemented HypothesisTestingStepsRunner.
    Other type of research projects can be implemented by creating a new StepsRunner class.
    The ToyStepsRunner is a cookie-cutter example of how to implement a new type of research project.
"""
# steps_runner_cls = ToyStepsRunner  # HypothesisTestingStepsRunner

"""
(2) Directory where the project is located. 
    Can be None to choose interactively (if using PySide app).
    Can be an abs path, or a relative path from `data_to_paper/projects`.
"""
# project_directory = None

"""
(3) Folder where the run recording and outputs will be saved.
    This folder will be created inside the project directory.
    If the folder already exists, data-to-paper will replay the recorded run
    until the end of the recording and then continue running the project.
"""
# run_folder = 'run_001'  # set to another value to create a new run for the same project

# Here are some examples of how to set the variables above:

# Example toy project:
# steps_runner_cls = ToyStepsRunner
# project_directory = 'toy_example/prime_numbers'
# run_folder = 'run_002'

# Hypothesis testing - interactive setup:
steps_runner_cls = HypothesisTestingStepsRunner
project_directory = None
run_folder = 'run_001'

# Hypothesis testing - diabetes project:
# steps_runner_cls = HypothesisTestingStepsRunner
# project_directory = 'diabetes/diabetes_open_goal'
# run_folder = 'run_001'

set_project_and_run(steps_runner_cls, project_directory=project_directory, run_folder=run_folder)
