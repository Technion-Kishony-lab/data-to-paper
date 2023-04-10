import os
import shutil
import glob
from pathlib import Path
from queries import data_description, goal_description

from scientistgpt import ScientificMentorGPT, ScientistGPT_EXECUTION_PLAN
from scientistgpt.run_gpt_code.dynamic_code import module_dir

"""
Set folders
"""
DATA_FOLDER = 'data_for_analysis'
MESSAGES_FILENAME = 'openai_exchange.txt'
OUTPUTS_FOLDER = 'run3'

# Get absolute paths:
absolute_output_path = Path(OUTPUTS_FOLDER).absolute()
absolute_data_path = Path(DATA_FOLDER).absolute()
absolute_home_path = Path().absolute()

# Create empty output folder (delete if exists):
if os.path.exists(absolute_output_path):
    shutil.rmtree(absolute_output_path)
os.makedirs(absolute_output_path)


"""
Run ScientificMentorGPT
"""
# we run in the data folder, so that chatgpt finds our files:
os.chdir(absolute_data_path)

runner = ScientificMentorGPT(execution_plan=ScientistGPT_EXECUTION_PLAN,
                             data_description=data_description,
                             goal_description=goal_description)

runner.run_all()

os.chdir(absolute_home_path)

"""
Save results
"""
# Save conversation to text file:
runner.conversation.save(absolute_output_path / MESSAGES_FILENAME)

# Move all gpt analysis result files to output folder:
for file in glob.glob(str(absolute_data_path / (ScientificMentorGPT.gpt_script_filename + '*.txt'))):
    shutil.move(file, absolute_output_path)

# Move all gpt analysis scripts to output folder:
for file in glob.glob(str(Path(module_dir) / (ScientificMentorGPT.gpt_script_filename + '*.py'))):
    shutil.move(file, absolute_output_path)

# Move all gpt generated plots to output folder:
for file in glob.glob(str(absolute_data_path / '*.png')):
    shutil.move(file, absolute_output_path)

# Move gpt generated txt files to output folder:
for file in glob.glob(str(absolute_data_path / '*.txt')):
    shutil.move(file, absolute_output_path)
