import shutil
import zipfile

from pathlib import Path
from typing import List, Optional

from data_to_paper.base_products import DataFileDescriptions, DataFileDescription
from data_to_paper.researches_types.scientific_research.run_steps import ScientificStepsRunner


THIS_FOLDER = Path(__file__).parent


def get_local_folder_path():
    from .local_paths import LOCAL_FOLDER_ROOT
    return Path(LOCAL_FOLDER_ROOT)


def read_file_description(directory: Path, filename: str):
    with open(directory / filename, 'r') as f:
        return f.read()


def read_general_file_description(directory: Path):
    return read_file_description(directory, 'general_description.txt')


def get_file_description(directory: Path, data_filename: str):
    return DataFileDescription(
        file_path=data_filename,
        description=read_file_description(directory, data_filename.split('.')[0] + '.txt'),
    )


def get_file_descriptions(input_directory: Path, data_filenames: List[str], data_folder: Path):
    return DataFileDescriptions([get_file_description(input_directory, data_filename)
                                 for data_filename in data_filenames],
                                data_folder=data_folder,
                                general_description=read_general_file_description(input_directory))


def copy_datafiles_to_data_folder(data_filenames: List[str], input_path: Path, data_folder: Path):
    """
    Clear temp data folder and copy data files from project folder to data folder
    """
    shutil.rmtree(data_folder, ignore_errors=True)  # remove data folder and all its content
    data_folder.mkdir(parents=True, exist_ok=True)  # create clean data folder
    for filename in data_filenames:
        if (input_path / filename).exists():
            # copy file to data folder
            shutil.copyfile(input_path / filename, data_folder / filename)
        elif (input_path / (filename + '.zip')).exists():
            # unzip file to data folder
            with zipfile.ZipFile(input_path / (filename + '.zip'), 'r') as zip_ref:
                zip_ref.extractall(data_folder)
        else:
            raise FileNotFoundError(f"File {filename} or {filename}.zip not found in {input_path}")


def get_output_path(project: str, output_folder: str, save_on_repo: bool = False) -> Path:
    if save_on_repo:
        return THIS_FOLDER / 'projects' / project / 'outputs' / output_folder
    else:
        return get_local_folder_path() / project / 'outputs' / output_folder


def get_input_path(project: str, load_from_repo: bool = False) -> Path:
    if load_from_repo:
        return THIS_FOLDER / 'projects' / project / 'inputs'
    else:
        return get_local_folder_path() / project


def get_paper(project: str, data_filenames: List[str], research_goal: Optional[str], output_folder: str,
              should_do_data_exploration: bool = True, should_mock_servers: bool = True,
              load_from_repo: bool = True,
              save_on_repo: bool = True):
    input_path = get_input_path(project, load_from_repo)
    temp_folder_to_run_in = input_path / 'temp_folder'
    copy_datafiles_to_data_folder(data_filenames, input_path, temp_folder_to_run_in)

    ScientificStepsRunner(
        data_file_descriptions=get_file_descriptions(input_path, data_filenames, temp_folder_to_run_in),
        research_goal=research_goal,
        output_directory=get_output_path(project, output_folder, save_on_repo),
        mock_servers=should_mock_servers,
        should_do_data_exploration=should_do_data_exploration,
    ).run_all_steps()
