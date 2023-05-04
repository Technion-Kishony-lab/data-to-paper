from g3pt import run_scientist_gpt
from queries_mimic import data_file_descriptions, simpler_research_goal

# local_path.py is git ignored. It should be created locally, and contain:
# DATA_FOLDER: absolute path to a directory where the data files are located
# OUTPUTS_FOLDER: absolute path to a directory where the output files will be saved

from local_paths import DATA_FOLDER, OUTPUT_FOLDER

run_scientist_gpt(data_file_descriptions=data_file_descriptions,
                  research_goal=simpler_research_goal,
                  data_directory=DATA_FOLDER,
                  output_directory=OUTPUT_FOLDER + '/out22',
                  mock_servers=True)  # <==== use True to mock/record openai responses
