import os
import importlib
import traceback
import warnings
from typing import Optional, List, Type

import chatgpt_created_scripts

from scientistgpt.env import MAX_EXEC_TIME

from .runtime_decorators import timeout_context
from .exceptions import FailedRunningCode

MODULE_NAME = 'script_to_run'

WARNINGS_TO_RAISE: List[Type[Warning]] = [RuntimeWarning, SyntaxWarning]
WARNINGS_TO_IGNORE: List[Type[Warning]] = [DeprecationWarning, ResourceWarning, PendingDeprecationWarning]

module_dir = os.path.dirname(chatgpt_created_scripts.__file__)
module_filename = MODULE_NAME + ".py"
module_filepath = os.path.join(module_dir, module_filename)


def save_code_to_module_file(code: str = None):
    code = code or '# empty module\n'
    with open(module_filepath, "w") as f:
        f.write(code)


# create module from empty file:
save_code_to_module_file()
module = importlib.import_module(chatgpt_created_scripts.__name__ + '.' + MODULE_NAME)


def run_code_using_module_reload(code: str, save_as: Optional[str] = None, timeout_sec: int = MAX_EXEC_TIME):
    """
    Run the provided code and report exceptions or specific warnings.

    Raises a TimeoutError exception if runs too long.

    To run the code, we save it to a .py file and use the importlib to import it.
    If the file was already imported before, we use importlib.reload.

    save_as: name of file to save the code.  None to skip saving.
    """

    save_code_to_module_file(code)
    with warnings.catch_warnings():
        for warning in WARNINGS_TO_IGNORE:
            warnings.filterwarnings("ignore", category=warning)
        for warning in WARNINGS_TO_RAISE:
            warnings.filterwarnings("error", category=warning)

        try:
            with timeout_context(timeout_sec):
                importlib.reload(module)
        except TimeoutError as e:
            # TODO:  add traceback to TimeoutError
            raise FailedRunningCode(exception=e, tb=None, code=code)
        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)
            raise FailedRunningCode(exception=e, tb=tb, code=code)
        finally:
            if save_as is None:
                save_code_to_module_file()
            else:
                os.rename(module_filepath, os.path.join(module_dir, save_as) + ".py")
