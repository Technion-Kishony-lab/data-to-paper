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

@dataclass(frozen=True)
class UnAllowedFilesCreated(PermissionError):
    un_allowed_files: List[str]

    def __str__(self):
        return f'UnAllowedFilesCreated: {self.un_allowed_files}'


@contextmanager
def run_in_temp_directory():
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


@contextmanager
def run_in_directory(folder: Union[Path, str] = None, allowed_create_files: Set[str] = None) -> Set[str]:
    """
    Run code in a specific folder.
    allowed_create_files is a set of file names that are allowed to be created in the folder.
    can also be a wildcard filename, e.g. '*.csv'.
    """
    cwd = os.getcwd()
    if folder is not None:
        os.chdir(folder)
    pre_existing_files = set(os.listdir())
    created_files = set()
    try:
        yield created_files
    finally:
        created_files.update(set(os.listdir()) - pre_existing_files)
        if allowed_create_files is not None:
            un_allowed_created_files = \
                [file for file in created_files
                 if not is_name_matches_list_of_wildcard_names(file, allowed_create_files)]
            if un_allowed_created_files:
                # delete created files:
                for file in un_allowed_created_files:
                    os.remove(file)
                raise UnAllowedFilesCreated(un_allowed_files=list(un_allowed_created_files))
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
