import shutil
from pathlib import Path
from typing import List, Optional

from scientistgpt.base_steps import DataFileDescriptions, DataFileDescription
from local_paths import LOCAL_FOLDER_ROOT
from scientistgpt.projects.scientific_research.run_steps import ScientificStepsRunner


LOCAL_PATH = Path(LOCAL_FOLDER_ROOT)

def read_file_description(project: str, filename: str):
    with open(LOCAL_PATH / project / (filename + '.txt'), 'r') as f:
        return f.read()


def get_file_description(project: str, filename: str):
    DataFileDescription(
        file_path=filename,
        description=read_file_description(project, filename),
    )


def get_file_descriptions(project: str, filenames: List[str]):
    return DataFileDescriptions([get_file_description(project, filename) for filename in filenames])


def get_paper(project: str, files: List[str], research_goal: Optional[str], output_folder: str,
              should_do_data_exploration: bool = True, should_mock_servers: bool = True):

    # copy files to temp folder:
    for filename in files:
        # copy file from Path(LOCAL_FOLDER_ROOT) / project / 'outputs'
        # to Path(LOCAL_FOLDER_ROOT) / 'temp':
        shutil.copyfile(LOCAL_PATH / project / 'outputs' / filename, LOCAL_PATH / 'temp' / filename)


    ScientificStepsRunner(
        data_file_descriptions=get_file_descriptions(project, files),
        research_goal=research_goal,
        output_directory=LOCAL_PATH / project / 'outputs' / output_folder,
        mock_servers=should_mock_servers,
        should_do_data_exploration=should_do_data_exploration,
    ).run_all_steps()
