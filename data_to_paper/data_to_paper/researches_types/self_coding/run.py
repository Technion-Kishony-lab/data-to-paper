from pathlib import Path

from data_to_paper.base_products import DataFileDescriptions
from run_steps import CodingStepsRunner

THIS_FOLDER = Path(__file__).parent

CodingStepsRunner(
    data_file_descriptions=DataFileDescriptions([], data_folder=THIS_FOLDER / 'data'),
    output_directory=THIS_FOLDER / 'output',
    mock_servers=True,
).run_all_steps()
