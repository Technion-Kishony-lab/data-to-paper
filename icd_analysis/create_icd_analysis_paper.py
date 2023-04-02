import os
import shutil
import glob
from pathlib import Path
from queries import data_description, goal_description

from scientistgpt import ScientistGPT, ScientistGPT_ANALYSIS_PLAN
from scientistgpt.dynamic_code import module_dir
from scientistgpt.gpt_interactors.scientist_gpt import GPT_SCRIPT_FILENAME

"""
Set folders
"""
DATA_FOLDER = 'data_for_analysis'
MESSAGES_FILENAME = 'openai_exchange.txt'
OUTPUTS_FOLDER = 'run1'

# Get absolute paths:
absolute_output_path = Path(OUTPUTS_FOLDER).absolute()
absolute_data_path = Path(DATA_FOLDER).absolute()
absolute_home_path = Path().absolute()

# Create empty output folder (delete if exists):
if os.path.exists(absolute_output_path):
    shutil.rmtree(absolute_output_path)
os.makedirs(absolute_output_path)


"""
Run ScientistGPT
"""
# we run in the data folder, so that chatgpt finds out files:
os.chdir(absolute_data_path)

runner = ScientistGPT(run_plan=ScientistGPT_ANALYSIS_PLAN,
                      data_description=data_description,
                      goal_description=goal_description)

runner.run_all(annotate=True)

os.chdir(absolute_home_path)

"""
Save results
"""
# Save conversation to text file:
runner.conversation.save(absolute_output_path / MESSAGES_FILENAME)

# Move all gpt analysis result files to output folder:
for file in glob.glob(str(absolute_data_path / (GPT_SCRIPT_FILENAME + '*.txt'))):
    shutil.move(file, absolute_output_path)

# Move all gpt analysis scripts to output folder:
for file in glob.glob(str(Path(module_dir) / (GPT_SCRIPT_FILENAME + '*.py'))):
    shutil.move(file, absolute_output_path)
