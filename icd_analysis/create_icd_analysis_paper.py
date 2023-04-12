import os
import shutil
import glob
from pathlib import Path
from queries import data_description, goal_description

from scientistgpt import ScientistGPT
from scientistgpt.conversation.replay import save_actions_to_file
from scientistgpt.run_gpt_code.dynamic_code import module_dir
from tests.utils import record_or_replay_openai

# local_path.py is git ignored. It should be created locally, and contain:
# DATA_FOLDER: absolute path to a directory where the data files are located
# OUTPUTS_FOLDER: absolute path to a directory where the output files will be saved

from icd_analysis.local_paths import DATA_FOLDER, OUTPUT_FOLDER

"""
Set folders
"""
ACTIONS_FILENAME = 'openai_exchange.txt'

# Get absolute paths:
absolute_output_path = Path(OUTPUT_FOLDER).absolute()
absolute_data_path = Path(DATA_FOLDER).absolute()
absolute_home_path = Path().absolute()

# Create empty output folder (delete if exists):
if os.path.exists(absolute_output_path):
    shutil.rmtree(absolute_output_path)
os.makedirs(absolute_output_path)


"""
Run ScientistGPT
"""

runner = ScientistGPT(data_description=data_description, goal_description=goal_description)


@record_or_replay_openai
def run_all():
    # we run in the data folder, so that chatgpt finds our files:
    os.chdir(absolute_data_path)
    runner.run_all()
    os.chdir(absolute_home_path)


run_all()

"""
Save results
"""
# Save conversation to text file:
save_actions_to_file(absolute_output_path / ACTIONS_FILENAME)

# Move all gpt analysis result files to output folder:
for file in glob.glob(str(absolute_data_path / (ScientistGPT.gpt_script_filename + '*.txt'))):
    shutil.move(file, absolute_output_path)

# Move all gpt analysis scripts to output folder:
for file in glob.glob(str(Path(module_dir) / (ScientistGPT.gpt_script_filename + '*.py'))):
    shutil.move(file, absolute_output_path)

# Move all gpt generated plots to output folder:
for file in glob.glob(str(absolute_data_path / '*.png')):
    shutil.move(file, absolute_output_path)

# TODO: this one is risky cs it might move our own data files (if they have .txt extension)
# Move gpt generated txt files to output folder:
for file in glob.glob(str(absolute_data_path / '*.txt')):
    shutil.move(file, absolute_output_path)
