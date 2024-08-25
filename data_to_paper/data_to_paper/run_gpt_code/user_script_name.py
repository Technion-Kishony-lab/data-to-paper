import os
import traceback

from data_to_paper.utils.mutable import Flag
from data_to_paper.env import BASE_FOLDER

MODULE_NAME = 'script_to_run'
module_filename = MODULE_NAME + ".py"


IS_CHECKING = Flag(False)


def is_filename_gpt_code(filename: str) -> bool:
    """
    Check if the filename is a gpt code filename or a test filename.
    """
    filename = os.path.basename(filename)
    return filename == module_filename


def is_filename_test(filename: str) -> bool:
    filename = os.path.basename(filename)
    return filename.startswith('test_')


def get_gpt_module_frames(tb: traceback.StackSummary) -> list:
    frames = [t for t in tb if is_filename_gpt_code(t.filename)]
    # frames = [t for t in tb if True]  # TODO: remove this line
    if len(frames):
        return frames
    frames = [t for t in tb if is_filename_test(t.filename)]
    return frames


def is_called_from_user_script(offset: int = 3) -> bool:
    """
    Check if the code is called from user script.
    """
    if IS_CHECKING:
        return False
    with IS_CHECKING.temporary_set(True):
        tb = traceback.extract_stack()
        filename = tb[-offset].filename
        return is_filename_gpt_code(filename) or is_filename_test(filename)


def is_called_from_data_to_paper(offset: int = 3) -> bool:
    """
    Check if the code is called from data_to_paper.
    """
    if IS_CHECKING:
        return False
    with IS_CHECKING.temporary_set(True):
        tb = traceback.extract_stack()
        filename = tb[-offset].filename
        return BASE_FOLDER.name in filename
