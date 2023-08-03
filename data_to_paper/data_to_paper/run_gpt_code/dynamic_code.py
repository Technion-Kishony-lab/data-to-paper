import builtins
from pathlib import Path

import matplotlib.pyplot as plt
import os
import importlib
import traceback
import warnings
from typing import Optional, List, Type, Tuple, Any, Union, Iterable

from data_to_paper import chatgpt_created_scripts

from data_to_paper.env import MAX_EXEC_TIME
from data_to_paper.utils.file_utils import run_in_directory, UnAllowedFilesCreated
from data_to_paper.run_gpt_code.overrides.dataframes import collect_created_and_changed_data_frames, DataframeOperations

from .run_context import prevent_calling, PreventFileOpen, PreventImport, runtime_access_to, get_runtime_object
from .runtime_decorators import timeout_context
from .exceptions import FailedRunningCode, BaseRunContextException
from .runtime_issues_collector import IssueCollector

MODULE_NAME = 'script_to_run'

WARNINGS_TO_RAISE: List[Type[Warning]] = [RuntimeWarning, SyntaxWarning]
WARNINGS_TO_IGNORE: List[Type[Warning]] = [DeprecationWarning, ResourceWarning, PendingDeprecationWarning,
                                           FutureWarning]
FORBIDDEN_MODULES_AND_FUNCTIONS = [
    # Module, function, create RunIssue (True) or raise exception (False)
    (builtins, 'print', True),
    (builtins, 'input', False),
    # (builtins, 'exec', False),
    (builtins, 'eval', False),
    (builtins, 'exit', False),
    (builtins, 'quit', False),
    (plt, 'savefig', False),
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


def get_prevent_calling_context():
    return get_runtime_object('prevent_calling_context')


def get_prevent_file_open_context() -> PreventFileOpen:
    return get_runtime_object('prevent_file_open_context')


def run_code_using_module_reload(
        code: str, save_as: Optional[str] = None,
        timeout_sec: int = None,
        warnings_to_raise: Iterable[Type[Warning]] = None,
        warnings_to_ignore: Iterable[Type[Warning]] = None,
        forbidden_modules_and_functions: Iterable[Tuple[Any, str, bool]] = None,
        allowed_read_files: Iterable[str] = None,
        allowed_write_files: Iterable[str] = None,
        allow_dataframes_to_change_existing_series: bool = True,
        runtime_available_objects: dict = None,
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

    prevent_calling_context = prevent_calling(forbidden_modules_and_functions)
    prevent_file_open_context = PreventFileOpen(allowed_read_files=allowed_read_files,
                                                allowed_write_files=allowed_write_files)

    runtime_available_objects = runtime_available_objects or {}
    runtime_available_objects['prevent_calling_context'] = prevent_calling_context
    runtime_available_objects['prevent_file_open_context'] = prevent_file_open_context

    save_code_to_module_file(code)
    with warnings.catch_warnings():
        for warning in warnings_to_ignore:
            warnings.filterwarnings("ignore", category=warning)
        for warning in warnings_to_raise:
            warnings.filterwarnings("error", category=warning)
        completed_successfully = False
        try:
            with timeout_context(timeout_sec), \
                    runtime_access_to(runtime_available_objects), \
                    prevent_calling_context, \
                    PreventImport(FORBIDDEN_IMPORTS), \
                    prevent_file_open_context, \
                    collect_created_and_changed_data_frames(
                        allow_dataframes_to_change_existing_series) as dataframe_operations, \
                    run_in_directory(run_in_folder, allowed_create_files=allowed_write_files) as created_files:
                importlib.reload(CODE_MODULE)
        except TimeoutError as e:
            # TODO:  add traceback to TimeoutError
            raise FailedRunningCode(exception=e, tb=None)
        except UnAllowedFilesCreated as e:
            raise FailedRunningCode(exception=e, tb=None)
        except BaseRunContextException as e:
            tb = traceback.extract_tb(e.__traceback__)
            tb.pop()  # remove the line of the context manager
            raise FailedRunningCode(exception=e, tb=tb)
        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)
            raise FailedRunningCode(exception=e, tb=tb)
        else:
            completed_successfully = True
        finally:
            if not completed_successfully:
                with run_in_directory(run_in_folder):
                    # remove all the files that were created
                    for file in created_files:
                        os.remove(file)
            if save_as:
                os.rename(module_filepath, os.path.join(module_dir, save_as) + ".py")
            save_code_to_module_file()
    return sorted(created_files), dataframe_operations
