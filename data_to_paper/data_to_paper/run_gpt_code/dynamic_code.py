import builtins
import pickle
from contextlib import ExitStack
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType

import os
import importlib

from typing import Optional, Type, Tuple, Any, Union, Iterable, Dict

from data_to_paper import llm_created_scripts

from data_to_paper.utils.file_utils import run_in_directory
from data_to_paper.utils.types import ListBasedSet

from .base_run_contexts import RunContext
from .attr_replacers import PreventCalling
from .run_contexts import PreventFileOpen, PreventImport, WarningHandler, IssueCollector, \
    TrackCreatedFiles

from .exceptions import FailedRunningCode, BaseRunContextException, CodeTimeoutException
from .timeout_context import timeout_context
from .user_script_name import MODULE_NAME, module_filename
from .run_issues import RunIssue, RunIssues
from data_to_paper.code_and_output_files.output_file_requirements import OutputFileRequirements
from data_to_paper.utils.singleton import undefined

module_dir = os.path.dirname(llm_created_scripts.__file__)
module_default_filepath = os.path.join(module_dir, module_filename)


def save_code_to_module_file(code: str = None):
    code = code or '# empty module\n'
    with open(module_default_filepath, "w") as f:
        f.write(code)


def generate_empty_code_module_object() -> ModuleType:
    """
    Generate module object with the given code and return it.
    """
    save_code_to_module_file()
    return importlib.import_module(llm_created_scripts.__name__ + '.' + MODULE_NAME)


def is_serializable(x):
    """
    Check if x is serializable so that it can be transferred between processes.
    """
    try:
        pickle.dumps(x)
        return True
    except TypeError:
        return False


# DEFAULT_WARNINGS_TO_ISSUE = (RuntimeWarning, SyntaxWarning, ConvergenceWarning)
DEFAULT_WARNINGS_TO_IGNORE = (DeprecationWarning, ResourceWarning, PendingDeprecationWarning, FutureWarning)
DEFAULT_WARNINGS_TO_RAISE = ()
DEFAULT_WARNINGS_TO_ISSUE = None  # None for all that are not ignored or raised

DEFAULT_FORBIDDEN_MODULES_AND_FUNCTIONS = (
        # Module, function, create RunIssue (True) or raise exception (False)
        (builtins, 'print', True),
        (builtins, 'input', False),
        (builtins, 'eval', False),
        (builtins, 'exit', False),
        (builtins, 'quit', False),
        # (builtins, 'exec', False),
    )

try:
    import matplotlib.pyplot as plt
    DEFAULT_FORBIDDEN_MODULES_AND_FUNCTIONS += ((plt, 'show', True),)
except ImportError:
    pass


DEFAULT_FORBIDDEN_IMPORTS = ('os', 'sys', 'subprocess', 'shutil', 'matplotlib')


@dataclass
class RunCode:
    """
    Run the provided code and report exceptions or specific warnings.
    """
    timeout_sec: Optional[int] = undefined
    warnings_to_issue: Optional[Iterable[Type[Warning]]] = undefined
    warnings_to_ignore: Optional[Iterable[Type[Warning]]] = undefined
    warnings_to_raise: Optional[Iterable[Type[Warning]]] = undefined

    forbidden_modules_and_functions: Iterable[Tuple[Any, str, bool]] = undefined
    forbidden_imports: Optional[Iterable[str]] = undefined

    # File lists can include wildcards, e.g. '*.py' or '**/*.py'. () means no files. None means all files.

    # Allowed in `open` for reading/writing
    allowed_open_read_files: Optional[Iterable[str]] = ()
    allowed_open_write_files: Optional[Iterable[str]] = ()

    # Allowed new files. Assessed at end of run. If None then all files are allowed.
    output_file_requirements: Optional[OutputFileRequirements] = OutputFileRequirements()

    run_folder: Union[Path, str] = field(default_factory=Path)

    additional_contexts: Optional[Dict[str, Any]] = None

    _module: ModuleType = None

    def __post_init__(self):
        if self.timeout_sec is undefined:
            self.timeout_sec = None
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
            contexts['timeout_context'] = timeout_context(self.timeout_sec, CodeTimeoutException)

        # Additional custom contexts:
        if self.additional_contexts is not None:
            for context_name, context in self.additional_contexts.items():
                assert context_name not in contexts, f"Context name {context_name} already exists."
                contexts[context_name] = context

        # name all contexts
        for name, context in contexts.items():
            context.name = name
        return contexts

    def run(self, code: Optional[str] = None, module_filepath: Optional[str] = None, save_as: Optional[str] = None,
            ) -> Tuple[Any, ListBasedSet[str], RunIssues, Dict[str, RunContext], Optional[FailedRunningCode]]:
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
            exception: an exception that was raised during the run, None if no exception was raised.
        """
        if module_filepath is None:
            self._module = generate_empty_code_module_object()
            save_code_to_module_file(code)

        contexts = self._create_and_get_all_contexts()
        exception = None
        result = None
        try:
            with ExitStack() as stack:
                for context in contexts.values():
                    stack.enter_context(context)
                try:
                    if module_filepath is None:
                        module = importlib.reload(self._module)
                    else:
                        module = importlib.import_module(module_filepath)
                    result = self._run_function_in_module(module)
                except RunIssue as e:
                    exception = e
                except Exception as e:
                    exception = FailedRunningCode.from_exception(e)

        except BaseRunContextException as e:
            exception = FailedRunningCode.from_exception(e)
        except Exception:
            raise
        finally:
            created_files = contexts['TrackCreatedFiles'].created_files
            if exception:
                with run_in_directory(self.run_folder):
                    # remove all the files that were created
                    for file in created_files:
                        if os.path.exists(file):
                            os.remove(file)
                created_files = []
            if save_as and module_filepath is None:
                os.rename(module_default_filepath, os.path.join(module_dir, save_as) + ".py")
            save_code_to_module_file()  # leave the module empty

        # Collect issues from all contexts
        issues = RunIssues()
        for context in contexts.values():
            if hasattr(context, 'issues'):
                issues.extend(context.issues)
        contexts = {name: context for name, context in contexts.items()
                    if isinstance(context, RunContext) and is_serializable(context)}

        return result, created_files, issues, contexts, exception

    def _run_function_in_module(self, module: ModuleType):
        pass
