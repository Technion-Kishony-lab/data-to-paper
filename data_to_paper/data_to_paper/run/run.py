# ============================================== #
# Main script for running data-to-paper projects #
# ============================================== #

from data_to_paper.research_types.scientific_research.steps_runner import ScientificStepsRunner
from data_to_paper.run.run_all_steps import set_project_and_run

# Currently using ScientificStepsRunner.
# Other type of research projects can be implemented by creating a new StepsRunner class.
steps_runner_cls = ScientificStepsRunner

# Directory where the project is located. Can be None to choose interactively (if using PySide app).
# Can be an abs path, or a relative path from `data_to_paper/projects`.
project_directory = 'diabetes/diabetes_open_goal'

# Folder where the run will be saved. This will be created inside the project directory.
# If the folder already exists, it will be replayed.
run_folder = 'run_001'

set_project_and_run(steps_runner_cls, project_directory=project_directory, run_folder=run_folder)
