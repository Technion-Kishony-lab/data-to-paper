import os
import shutil
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Union, List, Set

# Temp directory for latex complication:
module_dir = os.path.dirname(__file__)
TEMP_FOLDER = (Path(module_dir) / 'temp').absolute()


@dataclass(frozen=True)
class UnAllowedFilesCreated(PermissionError):
    un_allowed_files: List[str]

    def __str__(self):
        return f'UnAllowedFilesCreated: {self.un_allowed_files}'


@contextmanager
def run_in_temp_directory():
    cwd = os.getcwd()
    if not os.path.exists(TEMP_FOLDER):
        os.mkdir(TEMP_FOLDER)
    os.chdir(TEMP_FOLDER)
    try:
        yield
    finally:
        os.chdir(cwd)
        shutil.rmtree(TEMP_FOLDER)


@contextmanager
def run_in_directory(folder: Union[Path, str] = None, allowed_create_files: Set[str] = None):
    cwd = os.getcwd()
    if folder is not None:
        os.chdir(folder)
    pre_existing_files = set(os.listdir())
    try:
        yield
    finally:
        if allowed_create_files is not None:
            created_files = set(os.listdir()) - pre_existing_files
            un_allowed_created_files = created_files - set(allowed_create_files)
            if un_allowed_created_files:
                # delete created files:
                for file in un_allowed_created_files:
                    os.remove(file)
                raise UnAllowedFilesCreated(un_allowed_files=list(un_allowed_created_files))
        os.chdir(cwd)
