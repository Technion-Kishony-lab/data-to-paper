from pathlib import Path

from data_to_paper.research_types.scientific_research.steps_runner import ScientificStepsRunner
from data_to_paper.run.run_all_steps import run_all_steps

THIS_FOLDER = Path(__file__).parent

project_directory = THIS_FOLDER / 'diabetes_open_goal'
output_directory = project_directory / 'run_001'

step_runner = ScientificStepsRunner(
    project_directory=project_directory,
    output_directory=output_directory,
)


if __name__ == '__main__':
    run_all_steps(step_runner)
