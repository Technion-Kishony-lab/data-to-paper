from pathlib import Path

from data_to_paper.base_products import DataFileDescriptions, DataFileDescription
from data_to_paper.projects.demo_project.run_steps import DemoStepsRunner

THIS_FOLDER = Path(__file__).parent


DemoStepsRunner(
    data_file_descriptions=
    DataFileDescriptions(
        [DataFileDescription(file_path='number.txt', description="This file contains a large int, n.")],
        data_folder=THIS_FOLDER / 'data'),
    research_goal='Find the largest prime number smaller than the given natural number, n.',
    output_directory=THIS_FOLDER / 'output',
    mock_servers=True,
).run_all_steps()
