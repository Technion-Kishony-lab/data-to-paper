import os
import traceback

from data_to_paper.utils.mutable import Flag
from data_to_paper.env import BASE_FOLDER_NAME

MODULE_NAME = 'script_to_run'
module_filename = MODULE_NAME + ".py"


IS_CHECKING = Flag(False)


def is_called_from_user_script(offset: int = 3) -> bool:
    """
    Check if the code is called from user script.
    """
    if IS_CHECKING:
        return False
    with IS_CHECKING.temporary_set(True):
        tb = traceback.extract_stack()
        filename = os.path.basename(tb[-offset].filename)
        return filename == module_filename or filename.startswith('test_')


def is_called_from_data_to_paper(offset: int = 3) -> bool:
    """
    Check if the code is called from data_to_paper.
    """
    if IS_CHECKING:
        return False
    with IS_CHECKING.temporary_set(True):
        tb = traceback.extract_stack()
        filename = tb[-offset].filename
        return BASE_FOLDER_NAME in filename
