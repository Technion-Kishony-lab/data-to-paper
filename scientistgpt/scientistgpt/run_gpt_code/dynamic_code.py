import builtins
from pathlib import Path

import matplotlib.pyplot as plt
import os
import importlib
import traceback
import warnings
from typing import Optional, List, Type, Tuple, Any, Union, Set, Iterable

from scientistgpt import chatgpt_created_scripts

from scientistgpt.env import MAX_EXEC_TIME
from scientistgpt.utils.file_utils import run_in_directory, UnAllowedFilesCreated
from scientistgpt.run_gpt_code.overrides.dataframes import collect_created_and_changed_data_frames, DataframeOperations

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
        timeout_sec: int = None,
        warnings_to_raise: Iterable[Type[Warning]] = None,
        warnings_to_ignore: Iterable[Type[Warning]] = None,
        forbidden_modules_and_functions: Iterable[Tuple[Any, str]] = None,
        allowed_read_files: Iterable[str] = None,
        allowed_write_files: Iterable[str] = None,
        allow_dataframes_to_change_existing_series: bool = True,
        run_in_folder: Union[Path, str] = None) -> Tuple[List[str], DataframeOperations]:
    """
    Run the provided code and report exceptions or specific warnings.

    Raises a TimeoutError exception if runs too long.

    To run the code, we save it to a .py file and use the importlib to import it.
    If the file was already imported before, we use importlib.reload.

    save_as: name of file to save the code.  None to skip saving.
    """
    timeout_sec = timeout_sec or MAX_EXEC_TIME.val
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
                    collect_created_and_changed_data_frames(
                        allow_dataframes_to_change_existing_series) as dataframe_operations, \
                    run_in_directory(run_in_folder, allowed_create_files=allowed_write_files) as created_files:
                importlib.reload(CODE_MODULE)
        except TimeoutError as e:
            # TODO:  add traceback to TimeoutError
            raise FailedRunningCode(exception=e, tb=None, code=code)
        except UnAllowedFilesCreated as e:
            raise FailedRunningCode(exception=e, tb=None, code=code)
        except BaseRunContextException as e:
            tb = traceback.extract_tb(e.__traceback__)
            tb.pop()  # remove the line of the context manager
            raise FailedRunningCode(exception=e, tb=tb, code=code)
        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)
            raise FailedRunningCode(exception=e, tb=tb, code=code)
        finally:
            if save_as:
                os.rename(module_filepath, os.path.join(module_dir, save_as) + ".py")
            save_code_to_module_file()
    return sorted(created_files), dataframe_operations
