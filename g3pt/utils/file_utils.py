import os
import shutil
from contextlib import contextmanager
from pathlib import Path
from typing import Union

# Temp directory for latex complication:
module_dir = os.path.dirname(__file__)
TEMP_FOLDER = (Path(module_dir) / 'temp').absolute()


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
def run_in_directory(folder: Union[Path, str] = None):
    cwd = os.getcwd()
    if folder is not None:
        os.chdir(folder)
    try:
        yield
    finally:
        os.chdir(cwd)

