import pickle
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType

import os
import importlib

from typing import Optional, Type, Tuple, Any, Union, Iterable, Dict

from data_to_paper import llm_created_scripts

from data_to_paper.utils.file_utils import run_in_directory
from data_to_paper.utils.types import ListBasedSet

from .base_run_contexts import MultiRunContext
from .attr_replacers import PreventCalling
from .run_contexts import PreventFileOpen, ModifyImport, WarningHandler, IssueCollector, \
    TrackCreatedFiles, RunInDirectory

from .exceptions import FailedRunningCode, BaseRunContextException, CodeTimeoutException
from .timeout_context import timeout_context
from .user_script_name import MODULE_NAME, module_filename
from .run_issues import RunIssue
from data_to_paper.code_and_output_files.output_file_requirements import OutputFileRequirements

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
    except Exception:
        return False


@dataclass
class CodeRunner:
    """
    Run the provided code and report exceptions or specific warnings.
    """
    timeout_sec: Optional[int] = None
    warnings_to_ignore: Optional[Iterable[Type[Warning]]] = \
        (DeprecationWarning, ResourceWarning, PendingDeprecationWarning, FutureWarning)
    warnings_to_raise: Optional[Iterable[Type[Warning]]] = ()
    warnings_to_issue: Optional[Iterable[Type[Warning]]] = ...  # `...` for all that are not ignored or raised

    forbidden_modules_and_functions: Iterable[Tuple[Any, str, bool]] = \
        (
            # Module, function, create RunIssue (True) or raise exception (False)
            ('builtins', 'print', True),
            ('builtins', 'input', False),
            ('builtins', 'eval', False),
            ('builtins', 'exit', False),
            ('builtins', 'quit', False),
            ('matplotlib.pyplot', 'show', True),  # 'matplotlib.pyplot' is a string because it is not always installed
    )
    modified_imports: Tuple[Tuple[str, Optional[str]]] = (
            ('os', None),
            ('sys', None),
            ('subprocess', None),
            ('shutil', None),
    )

    # File lists can include wildcards, e.g. '*.py' or '**/*.py'. () means no files. None means all files.

    # Allowed in `open` for reading/writing
    allowed_open_read_files: Optional[Iterable[str]] = ()  # 'all' means all files. () means no files.
    allowed_open_write_files: Optional[Iterable[str]] = None  # 'all': all. `None`: Based on output_file_requirements

    # Allowed new files. Assessed at end of run. If None then all files are allowed.
    output_file_requirements: Optional[OutputFileRequirements] = OutputFileRequirements()

    run_folder: Union[Path, str] = field(default_factory=Path)

    additional_contexts: Optional[Dict[str, Any]] = field(default_factory=dict)

    _multi_context: MultiRunContext = None

    _module: ModuleType = None

    def _get_or_create_multi_context(self) -> MultiRunContext:
        if self._multi_context is not None:
            return self._multi_context

        allowed_open_write_files = self.allowed_open_write_files if self.allowed_open_write_files is not None \
            else self.output_file_requirements.get_all_allowed_created_filenames()

        # Mandatory contexts:
        contexts = {
            'RunInDirectory': RunInDirectory(folder=self.run_folder),
            'IssueCollector': IssueCollector(),
            'TrackCreatedFiles': TrackCreatedFiles(output_file_requirements=self.output_file_requirements),
        }

        # Optional builtin contexts:
        if self.forbidden_modules_and_functions is not None:
            contexts['PreventCalling'] = PreventCalling(modules_and_functions=self.forbidden_modules_and_functions)
        if self.modified_imports is not None:
            contexts['ModifyImport'] = ModifyImport(modified_imports=self.modified_imports)
        if not (self.allowed_open_read_files is None and allowed_open_write_files is None):
            contexts['PreventFileOpen'] = PreventFileOpen(allowed_read_files=self.allowed_open_read_files,
                                                          allowed_write_files=allowed_open_write_files)
        if not (self.warnings_to_raise is None and self.warnings_to_issue is None and self.warnings_to_ignore is None):
            contexts['WarningHandler'] = WarningHandler(categories_to_raise=self.warnings_to_raise,
                                                        categories_to_issue=self.warnings_to_issue,
                                                        categories_to_ignore=self.warnings_to_ignore)
        if self.timeout_sec is not None:
            contexts['TimeoutContext'] = timeout_context(self.timeout_sec, CodeTimeoutException)

        # Additional custom contexts:
        if self.additional_contexts is not None:
            for context_name, context in self.additional_contexts.items():
                assert context_name not in contexts, f"Context name {context_name} already exists."
                contexts[context_name] = context

        # name all contexts
        for name, context in contexts.items():
            context.name = name

        self._multi_context = MultiRunContext(contexts=contexts)
        return self._multi_context

    def run(self, code: Optional[str] = None, module_filepath: Optional[str] = None
            ) -> Tuple[Any, ListBasedSet[str], MultiRunContext, Optional[FailedRunningCode]]:
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

        multi_context = self._get_or_create_multi_context()
        exception = None
        result = None
        try:
            with multi_context:
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
            created_files = multi_context.contexts['TrackCreatedFiles'].created_files
            if exception:
                with run_in_directory(self.run_folder):
                    # remove all the files that were created
                    for file in created_files:
                        if os.path.exists(file):
                            os.remove(file)
            save_code_to_module_file()  # leave the module empty

        for context in multi_context.get_contexts():
            assert is_serializable(context), f"Context {context} is not serializable."

        return result, created_files, multi_context, exception

    def _run_function_in_module(self, module: ModuleType):
        pass
