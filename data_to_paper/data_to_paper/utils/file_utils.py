import os
import shutil
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Union, List, Set, Iterable
from fnmatch import fnmatch

# Get the path of the current folder:
THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))


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
    folder = os.path.join(THIS_FOLDER, str(uuid.uuid4()))
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
