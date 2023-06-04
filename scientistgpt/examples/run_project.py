import shutil
from pathlib import Path
from typing import List, Optional

from scientistgpt.base_products import DataFileDescriptions, DataFileDescription
from scientistgpt.projects.scientific_research.run_steps import ScientificStepsRunner
from .local_paths import LOCAL_FOLDER_ROOT


THIS_FOLDER = Path(__file__).parent

LOCAL_PATH = Path(LOCAL_FOLDER_ROOT)
TEMP_FOLDER_TO_RUN_IN = LOCAL_PATH / 'temp_folder'


def read_file_description(project: str, filename: str):
    with open(LOCAL_PATH / project / filename, 'r') as f:
        return f.read()


def read_general_file_description(project: str):
    return read_file_description(project, 'general_description.txt')


def get_file_description(project: str, data_filename: str):
    return DataFileDescription(
        file_path=data_filename,
        description=read_file_description(project, data_filename.split('.')[0] + '.txt'),
    )


def get_file_descriptions(project: str, data_filenames: List[str], data_folder: Path):
    return DataFileDescriptions([get_file_description(project, data_filename) for data_filename in data_filenames],
                                data_folder=data_folder,
                                general_description=read_general_file_description(project))


def copy_datafiles_to_data_folder(project: str, data_filenames: List[str], data_folder: Path):
    """
    Clear temp data folder and copy data files from project folder to data folder
    """
    # remove data folder and all its content:
    shutil.rmtree(data_folder, ignore_errors=True)
    # create clean data folder:
    data_folder.mkdir(parents=True, exist_ok=True)
    for filename in data_filenames:
        shutil.copyfile(LOCAL_PATH / project / filename, data_folder / filename)


def get_output_path(project: str, output_folder: str, save_on_repo: bool = False):
    if save_on_repo:
        return THIS_FOLDER / 'projects' / project / 'outputs' / output_folder
    else:
        return LOCAL_PATH / project / 'outputs' / output_folder


def get_paper(project: str, data_filenames: List[str], research_goal: Optional[str], output_folder: str,
              should_do_data_exploration: bool = True, should_mock_servers: bool = True,
              save_on_repo: bool = True):

    copy_datafiles_to_data_folder(project, data_filenames, TEMP_FOLDER_TO_RUN_IN)
    # clear temp folder and copy files to it:
    shutil.rmtree(TEMP_FOLDER_TO_RUN_IN / '*', ignore_errors=True)
    for filename in data_filenames:
        shutil.copyfile(LOCAL_PATH / project / filename, TEMP_FOLDER_TO_RUN_IN / filename)

    ScientificStepsRunner(
        data_file_descriptions=get_file_descriptions(project, data_filenames, TEMP_FOLDER_TO_RUN_IN),
        research_goal=research_goal,
        output_directory=get_output_path(project, output_folder, save_on_repo),
        mock_servers=should_mock_servers,
        should_do_data_exploration=should_do_data_exploration,
    ).run_all_steps()
