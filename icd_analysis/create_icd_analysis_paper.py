from pathlib import Path

from g3pt.projects.scientific_research.run_steps import ScientificStepsRunner
from queries_mimic import data_file_descriptions
# from queries_mimic import simpler_research_goal

# local_path.py is git ignored. It should be created locally, and contain:
# DATA_FOLDER: absolute path to a directory where the data files are located
# OUTPUTS_FOLDER: absolute path to a directory where the output files will be saved

from local_paths import DATA_FOLDER, OUTPUT_FOLDER
data_file_descriptions.data_folder = Path(DATA_FOLDER).absolute()

ScientificStepsRunner(
    data_file_descriptions=data_file_descriptions,
    research_goal=None,
    output_directory=OUTPUT_FOLDER + '/out3',
    mock_servers=True  # <==== use True to mock/record openai responses
).run_all_steps()
