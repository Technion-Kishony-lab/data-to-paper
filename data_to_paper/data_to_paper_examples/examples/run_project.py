import shutil
import zipfile

from pathlib import Path
from typing import List, Optional

from data_to_paper.base_products import DataFileDescriptions, DataFileDescription
from data_to_paper.latex.latex_doc import LatexDocument
from data_to_paper.research_types.scientific_research.run_steps import ScientificStepsRunner
from data_to_paper.research_types.scientific_research.scientific_products import HypertargetPrefix
from data_to_paper.utils.console_log_to_html import convert_console_log_to_html
from data_to_paper.utils.print_to_file import CONSOLE_LOG_FILE
from data_to_paper.code_and_output_files.referencable_text import NumericReferenceableText

THIS_FOLDER = Path(__file__).parent


def get_local_folder_path():
    from .local_paths import LOCAL_FOLDER_ROOT
    return Path(LOCAL_FOLDER_ROOT)


def read_file_description(directory: Path, filename: str):
    with open(directory / filename, 'r') as f:
        return f.read()


def read_general_file_description(directory: Path):
    return read_file_description(directory, 'general_description.txt')


def get_file_description(directory: Path, data_filename: str, file_num: int):
    description = read_file_description(directory, data_filename + '.description.txt')
    first_line = description.split('\n')[0]
    if first_line == 'TEXT':
        is_binary = False
    elif first_line == 'BINARY':
        is_binary = True
    else:
        is_binary = None
    if is_binary is not None:
        description = '\n'.join(description.split('\n')[1:])
    return DataFileDescription(
        file_path=data_filename,
        description=NumericReferenceableText(text=description,
                                             hypertarget_prefix=HypertargetPrefix.FILE_DESCRIPTIONS.value[file_num]),
        is_binary=is_binary,
    )


def get_file_descriptions(input_directory: Path, data_filenames: List[str], data_folder: Path):
    return DataFileDescriptions(
        [get_file_description(input_directory, data_filename, j) for j, data_filename in enumerate(data_filenames)],
        data_folder=data_folder,
        general_description=NumericReferenceableText(text=read_general_file_description(input_directory),
                                                     hypertarget_prefix=HypertargetPrefix.GENERAL_FILE_DESCRIPTION.value)
    )


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
              project_specific_goal_guidelines: Optional[str] = None,
              should_do_data_exploration: bool = True,
              excluded_citation_titles: List[str] = None,
              copy_openai_responses: bool = False,
              should_mock_servers: bool = True,
              load_from_repo: bool = True,
              should_remove_temp_folder: bool = True,
              save_on_repo: bool = True):
    input_path = get_input_path(project, load_from_repo)
    temp_folder_to_run_in = input_path / 'temp_folder'
    copy_datafiles_to_data_folder(data_filenames, input_path, temp_folder_to_run_in)

    output_directory = get_output_path(project, output_folder, save_on_repo)
    if copy_openai_responses and not output_directory.exists():
        copy_datafiles_to_data_folder(['openai_responses.txt'], input_path, output_directory)

    CONSOLE_LOG_FILE.set(output_directory / 'console_log.txt')

    ScientificStepsRunner(
        data_file_descriptions=get_file_descriptions(input_path, data_filenames, temp_folder_to_run_in),
        research_goal=research_goal,
        project_specific_goal_guidelines=project_specific_goal_guidelines or '',
        output_directory=output_directory,
        excluded_citation_titles=excluded_citation_titles,
        mock_servers=should_mock_servers,
        should_do_data_exploration=should_do_data_exploration,
        latex_document=LatexDocument(fontsize=11),
    ).run_all_steps()

    convert_console_log_to_html(CONSOLE_LOG_FILE.val)

    if should_remove_temp_folder:
        shutil.rmtree(temp_folder_to_run_in, ignore_errors=True)  # remove temp folder and all its content
