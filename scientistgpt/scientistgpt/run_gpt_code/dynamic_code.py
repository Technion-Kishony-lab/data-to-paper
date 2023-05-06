import builtins
from pathlib import Path

import matplotlib.pyplot as plt
import os
import importlib
import traceback
import warnings
from typing import Optional, List, Type, Tuple, Any, Union

import chatgpt_created_scripts

from scientistgpt.env import MAX_EXEC_TIME
from scientistgpt.utils.file_utils import run_in_directory

from .run_context import prevent_calling, prevent_file_open, PreventImport
from .runtime_decorators import timeout_context
from .exceptions import FailedRunningCode, BaseRunContextException

MODULE_NAME = 'script_to_run'

WARNINGS_TO_RAISE: List[Type[Warning]] = [RuntimeWarning, SyntaxWarning]
WARNINGS_TO_IGNORE: List[Type[Warning]] = [DeprecationWarning, ResourceWarning, PendingDeprecationWarning,
                                           FutureWarning]
FORBIDDEN_MODULES_AND_FUNCTIONS = [
    (builtins, 'print'),
    (builtins, 'input'),
    # (builtins, 'exec'),
    (builtins, 'eval'),
    (builtins, 'exit'),
    (builtins, 'quit'),
    (plt, 'savefig'),
]

FORBIDDEN_IMPORTS = [
    'os',
    'sys',
    'subprocess',
    'shutil',
    'pickle',
    'matplotlib',
]

module_dir = os.path.dirname(chatgpt_created_scripts.__file__)
module_filename = MODULE_NAME + ".py"
module_filepath = os.path.join(module_dir, module_filename)


def save_code_to_module_file(code: str = None):
    code = code or '# empty module\n'
    with open(module_filepath, "w") as f:
        f.write(code)


# create module from empty file:
save_code_to_module_file()
CODE_MODULE = importlib.import_module(chatgpt_created_scripts.__name__ + '.' + MODULE_NAME)


def run_code_using_module_reload(
        code: str, save_as: Optional[str] = None,
        timeout_sec: int = MAX_EXEC_TIME,
        warnings_to_raise: List[Type[Warning]] = None,
        warnings_to_ignore: List[Type[Warning]] = None,
        forbidden_modules_and_functions: List[Tuple[Any, str]] = None,
        allowed_read_files: List[str] = None,
        allowed_write_files: List[str] = None,
        run_in_folder: Union[Path, str] = None):
    """
    Run the provided code and report exceptions or specific warnings.

    Raises a TimeoutError exception if runs too long.

    To run the code, we save it to a .py file and use the importlib to import it.
    If the file was already imported before, we use importlib.reload.

    save_as: name of file to save the code.  None to skip saving.
    """

    warnings_to_raise = warnings_to_raise or WARNINGS_TO_RAISE
    warnings_to_ignore = warnings_to_ignore or WARNINGS_TO_IGNORE
    forbidden_modules_and_functions = forbidden_modules_and_functions or FORBIDDEN_MODULES_AND_FUNCTIONS

    save_code_to_module_file(code)
    with warnings.catch_warnings():
        for warning in warnings_to_ignore:
            warnings.filterwarnings("ignore", category=warning)
        for warning in warnings_to_raise:
            warnings.filterwarnings("error", category=warning)

        try:
            with timeout_context(timeout_sec), \
                    prevent_calling(forbidden_modules_and_functions), \
                    PreventImport(FORBIDDEN_IMPORTS), \
                    prevent_file_open(allowed_read_files, allowed_write_files), \
                    run_in_directory(run_in_folder):
                importlib.reload(CODE_MODULE)
        except TimeoutError as e:
            # TODO:  add traceback to TimeoutError
            raise FailedRunningCode(exception=e, tb=None, code=code)
        except BaseRunContextException as e:
            tb = traceback.extract_tb(e.__traceback__)
            tb.pop()  # remove the line of the context manager
            raise FailedRunningCode(exception=e, tb=tb, code=code)
        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)
            raise FailedRunningCode(exception=e, tb=tb, code=code)
        finally:
            if save_as is None:
                save_code_to_module_file()
            else:
                os.rename(module_filepath, os.path.join(module_dir, save_as) + ".py")
