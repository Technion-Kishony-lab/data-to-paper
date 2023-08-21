import builtins
from contextlib import ExitStack
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType

import matplotlib.pyplot as plt
import os
import importlib

from typing import Optional, Type, Tuple, Any, Union, Iterable, Dict, Callable

from data_to_paper import chatgpt_created_scripts

from data_to_paper.env import MAX_EXEC_TIME
from data_to_paper.utils.file_utils import run_in_directory
from data_to_paper.utils.types import ListBasedSet

from .base_run_contexts import RunContext
from .run_contexts import PreventCalling, PreventFileOpen, PreventImport, WarningHandler, ProvideData, IssueCollector, \
    TrackCreatedFiles
from .timeout_context import timeout_context
from .exceptions import FailedRunningCode, BaseRunContextException
from .types import module_filename, MODULE_NAME, RunIssues, OutputFileRequirements
from ..utils.singleton import undefined

module_dir = os.path.dirname(chatgpt_created_scripts.__file__)
module_filepath = os.path.join(module_dir, module_filename)


def save_code_to_module_file(code: str = None):
    code = code or '# empty module\n'
    with open(module_filepath, "w") as f:
        f.write(code)


# create module from empty file:
save_code_to_module_file()
CODE_MODULE = importlib.import_module(chatgpt_created_scripts.__name__ + '.' + MODULE_NAME)

DEFAULT_WARNINGS_TO_ISSUE = (RuntimeWarning, SyntaxWarning)
DEFAULT_WARNINGS_TO_IGNORE = (DeprecationWarning, ResourceWarning, PendingDeprecationWarning, FutureWarning)
DEFAULT_WARNINGS_TO_RAISE = ()

DEFAULT_FORBIDDEN_MODULES_AND_FUNCTIONS = (
        # Module, function, create RunIssue (True) or raise exception (False)
        (builtins, 'print', True),
        (builtins, 'input', False),
        (builtins, 'eval', False),
        (builtins, 'exit', False),
        (builtins, 'quit', False),
        (plt, 'savefig', False),
        # (builtins, 'exec', False),
    )

DEFAULT_FORBIDDEN_IMPORTS = ('os', 'sys', 'subprocess', 'shutil', 'matplotlib')


@dataclass
class RunCode:
    """
    Run the provided code and report exceptions or specific warnings.
    """
    timeout_sec: int = undefined
    warnings_to_issue: Iterable[Type[Warning]] = undefined
    warnings_to_ignore: Iterable[Type[Warning]] = undefined
    warnings_to_raise: Iterable[Type[Warning]] = undefined

    forbidden_modules_and_functions: Iterable[Tuple[Any, str, bool]] = undefined
    forbidden_imports: Optional[Iterable[str]] = undefined

    # File lists can include wildcards, e.g. '*.py' or '**/*.py'. () means no files. None means all files.

    # Allowed in `open` for reading/writing
    allowed_open_read_files: Optional[Iterable[str]] = ()
    allowed_open_write_files: Optional[Iterable[str]] = ()

    # Allowed new files. Assessed at end of run. If None then all files are allowed.
    output_file_requirements: Optional[OutputFileRequirements] = OutputFileRequirements()

    runtime_available_objects: Optional[Dict] = None
    run_folder: Union[Path, str] = field(default_factory=Path)

    additional_contexts: Optional[Callable[[], Dict[str, Any]]] = None

    def __post_init__(self):
        if self.timeout_sec is undefined:
            self.timeout_sec = MAX_EXEC_TIME.val
        if self.warnings_to_issue is undefined:
            self.warnings_to_issue = DEFAULT_WARNINGS_TO_ISSUE
        if self.warnings_to_ignore is undefined:
            self.warnings_to_ignore = DEFAULT_WARNINGS_TO_IGNORE
        if self.warnings_to_raise is undefined:
            self.warnings_to_raise = DEFAULT_WARNINGS_TO_RAISE
        if self.forbidden_modules_and_functions is undefined:
            self.forbidden_modules_and_functions = DEFAULT_FORBIDDEN_MODULES_AND_FUNCTIONS
        if self.forbidden_imports is undefined:
            self.forbidden_imports = DEFAULT_FORBIDDEN_IMPORTS

    def _create_and_get_all_contexts(self) -> Dict[str, Any]:

        # Mandatory contexts:
        contexts = {
            'run_in_directory': run_in_directory(self.run_folder),
            'IssueCollector': IssueCollector(),
            'TrackCreatedFiles': TrackCreatedFiles(output_file_requirements=self.output_file_requirements),
        }

        # Optional builtin contexts:
        if self.runtime_available_objects is not None:
            contexts['ProvideData'] = ProvideData(data=self.runtime_available_objects)
        if self.forbidden_modules_and_functions is not None:
            contexts['PreventCalling'] = PreventCalling(modules_and_functions=self.forbidden_modules_and_functions)
        if self.forbidden_imports is not None:
            contexts['PreventImport'] = PreventImport(modules=self.forbidden_imports)
        if not (self.allowed_open_read_files is None and self.allowed_open_write_files is None):
            contexts['PreventFileOpen'] = PreventFileOpen(allowed_read_files=self.allowed_open_read_files,
                                                          allowed_write_files=self.allowed_open_write_files)
        if not (self.warnings_to_raise is None and self.warnings_to_issue is None and self.warnings_to_ignore is None):
            contexts['WarningHandler'] = WarningHandler(categories_to_raise=self.warnings_to_raise,
                                                        categories_to_issue=self.warnings_to_issue,
                                                        categories_to_ignore=self.warnings_to_ignore)
        if self.timeout_sec is not None:
            contexts['timeout_context'] = timeout_context(seconds=self.timeout_sec)

        # Additional custom contexts:
        if self.additional_contexts is not None:
            for context_name, context in self.additional_contexts().items():
                assert context_name not in contexts, f"Context name {context_name} already exists."
                contexts[context_name] = context
        return contexts

    def run(self, code: str, save_as: Optional[str] = None
            ) -> Tuple[Any, ListBasedSet[str], RunIssues, Dict[str, Any]]:
        """
        Run the provided code and report exceptions or specific warnings.

        To run the code, we save it to a .py file and use the importlib to import it.
        If the file was already imported before, we use importlib.reload.

        save_as: name of file to save the code.  None to skip saving.

        Returns:
            result: the result of a call to a function in the code, None if no function was called.
            created_files: the files that were created during the run.
            issues: the issues that were found during the run.
            contexts: a dict of all the contexts within which the code was run.
        """
        contexts = self._create_and_get_all_contexts()
        save_code_to_module_file(code)
        completed_successfully = False
        result = None
        try:
            with ExitStack() as stack:
                for context in contexts.values():
                    stack.enter_context(context)
                try:
                    module = importlib.reload(CODE_MODULE)
                    result = self._run_function_in_module(module)
                except Exception as e:
                    raise FailedRunningCode.from_exception(e)

        except BaseRunContextException as e:
            raise FailedRunningCode.from_exception(e)
        except Exception:
            raise
        else:
            completed_successfully = True
        finally:
            created_files = contexts['TrackCreatedFiles'].created_files
            if not completed_successfully:
                with run_in_directory(self.run_folder):
                    # remove all the files that were created
                    for file in created_files:
                        os.remove(file)
            if save_as:
                os.rename(module_filepath, os.path.join(module_dir, save_as) + ".py")
            save_code_to_module_file()  # leave the module empty

        # Collect issues from all contexts
        issues = RunIssues()
        for context in contexts.values():
            if isinstance(context, RunContext):
                issues.extend(context.issues)

        return result, created_files, issues, contexts

    def _run_function_in_module(self, module: ModuleType):
        pass
