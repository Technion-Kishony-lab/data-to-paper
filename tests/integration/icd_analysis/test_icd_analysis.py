import os
import shutil
import glob
from pathlib import Path

import pytest

from scientistgpt.conversation.conversation import OPENAI_SERVER_CALLER
from icd_analysis.queries_mimic import data_file_descriptions, research_goal

from scientistgpt.run_gpt_code.dynamic_code import module_dir

# TODO:  adapt this test to the new step-by-step code

"""
Set folders
"""
DATA_FOLDER = 'data_for_analysis'
MESSAGES_FILENAME = 'openai_exchange.txt'
OUTPUTS_FOLDER = 'run3'

# Get absolute paths relative to this file:
absolute_home_path = Path(__file__).parent
absolute_output_path = absolute_home_path / OUTPUTS_FOLDER
absolute_data_path = absolute_home_path / DATA_FOLDER

# Create empty output folder (delete if exists):
if os.path.exists(absolute_output_path):
    shutil.rmtree(absolute_output_path)
os.makedirs(absolute_output_path)


@pytest.mark.skip
@OPENAI_SERVER_CALLER.record_or_replay()
def test_icd_analysis():
    # we run in the data folder, so that chatgpt finds our files:
    os.chdir(absolute_data_path)

    runner = ScientistGPT(data_file_descriptions=data_file_descriptions, research_goal=research_goal)

    runner.run_all()

    os.chdir(absolute_home_path)

    """
    Save results
    """
    # Save conversation to text file:
    runner.conversation.save(absolute_output_path / MESSAGES_FILENAME)

    # Move all gpt analysis result files to output folder:
    for file in glob.glob(str(absolute_data_path / (ScientistGPT.gpt_script_filename + '*.txt'))):
        shutil.move(file, absolute_output_path)

    # Move all gpt analysis scripts to output folder:
    for file in glob.glob(str(Path(module_dir) / (ScientistGPT.gpt_script_filename + '*.py'))):
        shutil.move(file, absolute_output_path)

    # Move all gpt generated plots to output folder:
    for file in glob.glob(str(absolute_data_path / '*.png')):
        shutil.move(file, absolute_output_path)

    # Move gpt generated txt files to output folder:
    for file in glob.glob(str(absolute_data_path / '*.txt')):
        shutil.move(file, absolute_output_path)
