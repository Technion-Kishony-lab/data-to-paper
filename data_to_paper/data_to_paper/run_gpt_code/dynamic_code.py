import builtins
from pathlib import Path

import matplotlib.pyplot as plt
import os
import importlib
import traceback

from typing import Optional, List, Type, Tuple, Any, Union, Iterable

from data_to_paper import chatgpt_created_scripts

from data_to_paper.env import MAX_EXEC_TIME
from data_to_paper.utils.file_utils import run_in_directory, UnAllowedFilesCreated
from data_to_paper.run_gpt_code.overrides.dataframes import collect_created_and_changed_data_frames, DataframeOperations
from .overrides.contexts import override_statistics_packages

from .run_context import PreventCalling, PreventFileOpen, PreventImport, WarningHandler, ProvideData, IssueCollector
from .timeout_context import timeout_context
from .exceptions import FailedRunningCode, BaseRunContextException
from .types import module_filename, MODULE_NAME

WARNINGS_TO_ISSUE: List[Type[Warning]] = [RuntimeWarning, SyntaxWarning]
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
        warnings_to_issue: Iterable[Type[Warning]] = None,
        warnings_to_ignore: Iterable[Type[Warning]] = None,
        warnings_to_raise: Iterable[Type[Warning]] = None,
        forbidden_modules_and_functions: Iterable[Tuple[Any, str, bool]] = None,
        allowed_read_files: Iterable[str] = None,
        allowed_write_files: Iterable[str] = None,
        allow_dataframes_to_change_existing_series: bool = True,
        runtime_available_objects: dict = None,
        run_in_folder: Union[Path, str] = None) -> Tuple[List[str], DataframeOperations, IssueCollector]:
    """
    Run the provided code and report exceptions or specific warnings.

    Raises a TimeoutError exception if runs too long.

    To run the code, we save it to a .py file and use the importlib to import it.
    If the file was already imported before, we use importlib.reload.

    save_as: name of file to save the code.  None to skip saving.
    """
    timeout_sec = timeout_sec or MAX_EXEC_TIME.val
    warnings_to_issue = warnings_to_issue or WARNINGS_TO_ISSUE
    warnings_to_ignore = warnings_to_ignore or WARNINGS_TO_IGNORE
    warnings_to_raise = warnings_to_raise or []
    forbidden_modules_and_functions = forbidden_modules_and_functions or FORBIDDEN_MODULES_AND_FUNCTIONS

    runtime_available_objects = runtime_available_objects or {}

    save_code_to_module_file(code)
    completed_successfully = False
    try:
        with \
                ProvideData(data=runtime_available_objects), \
                PreventCalling(modules_and_functions=forbidden_modules_and_functions), \
                PreventImport(modules=FORBIDDEN_IMPORTS), \
                PreventFileOpen(allowed_read_files=allowed_read_files, allowed_write_files=allowed_write_files), \
                WarningHandler(categories_to_raise=warnings_to_raise,
                               categories_to_issue=warnings_to_issue, categories_to_ignore=warnings_to_ignore), \
                IssueCollector() as issue_collector, \
                collect_created_and_changed_data_frames(
                    allow_dataframes_to_change_existing_series) as dataframe_operations, \
                timeout_context(seconds=timeout_sec), \
                override_statistics_packages(), \
                run_in_directory(run_in_folder, allowed_create_files=allowed_write_files) as created_files:
            try:
                importlib.reload(CODE_MODULE)
            except Exception as e:
                raise FailedRunningCode.from_exception(e)

    except (TimeoutError, UnAllowedFilesCreated, BaseRunContextException) as e:
        raise FailedRunningCode.from_exception(e)
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
    return sorted(created_files), dataframe_operations, issue_collector
