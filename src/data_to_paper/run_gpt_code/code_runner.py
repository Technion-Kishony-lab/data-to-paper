import pickle
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType

import os
import importlib

from typing import Optional, Type, Tuple, Any, Union, Iterable, Dict, Callable

from data_to_paper.env import DEBUG_MODE
from data_to_paper.utils.types import ListBasedSet
from data_to_paper.code_and_output_files.output_file_requirements import OutputFileRequirements

from .base_run_contexts import MultiRunContext
from .attr_replacers import PreventCalling
from .config import configure_matplotlib
from .run_contexts import PreventFileOpen, ModifyImport, WarningHandler, IssueCollector, \
    TrackCreatedFiles, RunInDirectory

from .exceptions import FailedRunningCode, BaseRunContextException
from .user_script_name import MODULE_NAME, module_filename
from .run_issues import RunIssue

from data_to_paper import llm_created_scripts
module_dir = os.path.dirname(llm_created_scripts.__file__)
module_default_filepath = os.path.join(module_dir, module_filename)

USING_MATPLOTLIB_IN_GPT_CODE = False


def save_code_to_module_file(code: str = None):
    code = code or '# empty module\n'
    with open(module_default_filepath, "w", encoding='utf-8') as f:
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

    _module: Optional[ModuleType] = None

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
                                                          allowed_write_files=allowed_open_write_files,
                                                          allowed_write_folder=self.run_folder)
        if not (self.warnings_to_raise is None and self.warnings_to_issue is None and self.warnings_to_ignore is None):
            contexts['WarningHandler'] = WarningHandler(categories_to_raise=self.warnings_to_raise,
                                                        categories_to_issue=self.warnings_to_issue,
                                                        categories_to_ignore=self.warnings_to_ignore)
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

    def run(self, code: Union[str, Callable, ModuleType]
            ) -> Tuple[Any, ListBasedSet[str], MultiRunContext, Optional[FailedRunningCode]]:
        """
        Run the provided code and report exceptions or specific warnings.

        `code` can be provided as:
        - a string of code to run,
            To run the code, we save it to a .py file and use the importlib to import it.
        - a function to run,
            The function is called in the current context.
        - a module to run,
            The module is reloaded and the function is called in the current context.

        Returns:
            result: the result of a call to a function in the code, None if no function was called.
            created_files: the files that were created during the run.
            multi_context: the multi context that was used during the run.
            exception: an exception that was raised during the run, None if no exception was raised.
        """
        if USING_MATPLOTLIB_IN_GPT_CODE:
            configure_matplotlib()

        if isinstance(code, str):
            self._module = generate_empty_code_module_object()
            save_code_to_module_file(code)
        elif isinstance(code, ModuleType):
            self._module = code
        else:
            self._module = None

        multi_context = self._get_or_create_multi_context()
        exception = None
        result = None
        try:
            with multi_context:
                try:
                    if self._module is None:
                        result = code()
                    else:
                        module = importlib.reload(self._module)
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
            if not DEBUG_MODE:
                save_code_to_module_file()  # leave the module empty

        for context in multi_context.get_contexts():
            assert is_serializable(context), f"Context {context} is not serializable."

        created_files = multi_context.contexts['TrackCreatedFiles'].created_files
        return result, created_files, multi_context, exception

    def _run_function_in_module(self, module: ModuleType):
        pass
