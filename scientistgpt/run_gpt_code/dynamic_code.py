import os
import importlib
import traceback
from typing import Optional

import chatgpt_created_scripts

from scientistgpt.env import MAX_EXEC_TIME

from .runtime_decorators import timeout
from .exceptions import FailedRunningCode

MODULE_NAME = 'script_to_run'


module_dir = os.path.dirname(chatgpt_created_scripts.__file__)
module_filename = MODULE_NAME + ".py"
module_filepath = os.path.join(module_dir, module_filename)


def save_code_to_module_file(code: str):
    with open(module_filepath, "w") as f:
        f.write(code)


# create module from empty file:
save_code_to_module_file('# empty module\n')
module = importlib.import_module(chatgpt_created_scripts.__name__ + '.' + MODULE_NAME)


@timeout(MAX_EXEC_TIME)
def run_code_from_file(code: str, save_as: Optional[str]):
    """
    Run the provided code by saving to a file and importing.

    Raises a TimeoutError exception if runs too long.

    To run the code, we save it to a .py file and use the importlib to import it.
    If the file was already imported before, we use importlib.reload.

    save_as: name of file to save the code.  None to skip saving.
    """

    save_code_to_module_file(code)
    try:
        importlib.reload(module)
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        raise FailedRunningCode(exception=e, tb=tb, code=code)
    finally:
        if save_as is None:
            os.remove(module_filepath)
        else:
            os.rename(module_filepath, os.path.join(module_dir, save_as) + ".py")
