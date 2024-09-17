import os
import shutil
import tempfile
import uuid
import re
from contextlib import contextmanager
from pathlib import Path
from typing import Union, Iterable
from fnmatch import fnmatch


def is_valid_filename(filename):
    # Regular expression for validating the filename
    pattern = r'^[a-zA-Z0-9_-]+$'
    # Match the pattern with the filename
    if re.match(pattern, filename):
        return True
    else:
        return False


def clear_directory(directory: Union[Path, str], create_if_missing: bool = True):
    """
    Clear the directory of all files and subdirectories.
    """
    directory = Path(directory)
    if not directory.exists():
        if create_if_missing:
            directory.mkdir(parents=True)
        else:
            raise FileNotFoundError(f'Directory {directory} does not exist.')
    for item in directory.iterdir():
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()


def is_name_matches_list_of_wildcard_names(file_name: str, list_of_filenames: Iterable[str]):
    """
    Check if file_name matches any of the wildcard filenames in list_of_filenames.
    Wildcard filenames are filenames that end with '*'.
    The wildcard '*' can be in the beginning or in the end of the filename.
    """
    for wildcard_filename in list_of_filenames:
        if fnmatch(file_name, wildcard_filename):
            return True
    return False


@contextmanager
def run_in_temp_directory():
    """
    Run code in a temporary folder.
    The folder is deleted after the code is done running.
    """
    cwd = os.getcwd()
    folder = os.path.join(tempfile.gettempdir(), f'data_to_paper_temp_{uuid.uuid4()}')
    if not os.path.exists(folder):
        os.mkdir(folder)
    os.chdir(folder)
    try:
        yield folder
    finally:
        os.chdir(cwd)
        shutil.rmtree(folder)


# context manager to run in a given directory:
@contextmanager
def run_in_directory(folder: Union[Path, str] = None) -> Union[Path, str]:
    """
    Run code in a specific folder.
    If folder is None, run in the current folder.
    """
    cwd = os.getcwd()
    if folder is not None:
        os.chdir(folder)
    try:
        yield folder
    finally:
        os.chdir(cwd)


def get_non_existing_file_name(file_path: Union[Path, str]) -> Union[Path, str]:
    """
    If file_path already exists, add a number to the end of the file name.
    """
    file_path = Path(file_path)
    i = 0
    while True:
        new_file_path = file_path.with_name(f'{file_path.stem}_{i}{file_path.suffix}')
        if not new_file_path.exists():
            return new_file_path
        i += 1
