from scientistgpt import run_scientist_gpt, view_saved_conversation
from queries import data_description, goal_description

# local_path.py is git ignored. It should be created locally, and contain:
# DATA_FOLDER: absolute path to a directory where the data files are located
# OUTPUTS_FOLDER: absolute path to a directory where the output files will be saved

from icd_analysis.local_paths import DATA_FOLDER, OUTPUT_FOLDER

run_scientist_gpt(data_description=data_description,
                  goal_description=goal_description,
                  data_directory=DATA_FOLDER,
                  output_directory=OUTPUT_FOLDER)
