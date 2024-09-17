import os
import traceback

from pathlib import Path

from data_to_paper.utils.mutable import Flag

MODULE_NAME = 'script_to_run'
module_filename = MODULE_NAME + ".py"


IS_CHECKING = Flag(False)


def is_filename_gpt_code(filename: str) -> bool:
    """
    Check if the filename is a gpt code filename or a test filename.
    """
    folder = Path(filename).parent
    filename = os.path.basename(filename)
    # TODO: this is a hack. Need to define the file of the gpt script dynamically.
    return filename == module_filename \
        or str(folder).replace('\\', '/').endswith('data_to_paper/scripts')


def is_filename_test(filename: str) -> bool:
    filename = os.path.basename(filename)
    return filename.startswith('test_')


def get_gpt_module_frames(tb: traceback.StackSummary) -> list:
    frames = [t for t in tb if is_filename_gpt_code(t.filename)]
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
        tb = traceback.extract_stack()  # this can lead to import and invoke recursion (thereby IS_CHECKING))
        filename = tb[-offset].filename
        return is_filename_gpt_code(filename) or is_filename_test(filename)
