from __future__ import annotations

import builtins
import os
import warnings

from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Tuple, Any, Iterable, Callable, List, Type, Dict, Optional

from data_to_paper.utils.file_utils import is_name_matches_list_of_wildcard_names
from data_to_paper.utils.types import ListBasedSet
from data_to_paper.utils import dedent_triple_quote_str

from .exceptions import CodeUsesForbiddenFunctions, CodeWriteForbiddenFile, CodeReadForbiddenFile, \
    CodeImportForbiddenModule, UnAllowedFilesCreated, FailedRunningCode
from .types import CodeProblem, RunIssue, OutputFileRequirements
from .base_run_contexts import SingletonRegisteredRunContext


@dataclass
class ProvideData(SingletonRegisteredRunContext):
    data: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def get_item(cls, key: str) -> Any:
        self = cls.get_runtime_instance()
        return self.data[key]

    @classmethod
    def set_item(cls, key: str, value: Any):
        self = cls.get_runtime_instance()
        self.data[key] = value

    @classmethod
    def get_or_create_item(cls, key: str, value: Any):
        self = cls.get_runtime_instance()
        if key not in self.data:
            self.data[key] = value
        return self.data[key]


@dataclass
class IssueCollector(SingletonRegisteredRunContext):
    pass


@dataclass
class PreventFileOpen(SingletonRegisteredRunContext):
    SYSTEM_FILES = ['templates/latex_table.tpl', 'templates/latex_longtable.tpl']
    SYSTEM_FOLDERS = \
        [r'C:\Windows', r'C:\Program Files', r'C:\Program Files (x86)'] if os.name == 'nt' \
        else ['/usr', '/etc', '/bin', '/sbin', '/sys', '/dev', '/var', '/opt', '/proc']
    TEMPORARILY_DISABLE_IS_INTERNAL_ONLY = False
    allowed_read_files: Iterable[str] = None  # list of wildcard names,  None means allow all, [] means allow none
    allowed_write_files: Iterable[str] = None  # list of wildcard names,  None means allow all, [] means allow none

    original_open: Callable = None

    def _reversible_enter(self):
        self.original_open = builtins.open
        builtins.open = self.open_wrapper
        return super()._reversible_enter()

    def _reversible_exit(self):
        builtins.open = self.original_open
        return super()._reversible_exit()

    def is_allowed_read_file(self, file_name: str) -> bool:
        return self.allowed_read_files is None or \
            is_name_matches_list_of_wildcard_names(file_name, self.allowed_read_files) or \
            self._is_system_file(file_name)

    def is_allowed_write_file(self, file_name: str) -> bool:
        return self.allowed_write_files is None or \
            is_name_matches_list_of_wildcard_names(file_name, self.allowed_write_files)

    def open_wrapper(self, *args, **kwargs):
        file_name = args[0] if len(args) > 0 else kwargs.get('file', None)
        open_mode = args[1] if len(args) > 1 else kwargs.get('mode', 'r')
        is_opening_for_writing = open_mode in ['w', 'a', 'x', 'wb']
        if is_opening_for_writing:
            if not self.is_allowed_write_file(file_name):
                raise CodeWriteForbiddenFile(file=file_name)
        else:
            if not self.is_allowed_read_file(file_name) \
                    and not PreventImport.get_runtime_instance(). \
                    is_currently_importing():  # allow read files when importing packages
                raise CodeReadForbiddenFile(file=file_name)
        return self.original_open(*args, **kwargs)

    def _is_system_file(self, file_name):
        abs_path_to_file = os.path.abspath(file_name)
        return any(abs_path_to_file.startswith(folder) for folder in self.SYSTEM_FOLDERS) or \
            any(abs_path_to_file.endswith(file) for file in self.SYSTEM_FILES)


@dataclass
class TrackCreatedFiles(SingletonRegisteredRunContext):
    output_file_requirements: Optional[OutputFileRequirements] = None  # None means allow all

    created_files: Optional[ListBasedSet[str]] = None  # None - unknown, context is not yet exited
    un_allowed_created_files: Optional[List[str]] = None  # None - unknown, context is not yet exited
    _preexisting_files: ListBasedSet[str] = None

    def __enter__(self):
        self._preexisting_files = ListBasedSet(os.listdir())
        self.created_files = None
        self.un_allowed_created_files = None
        return super().__enter__()

    def _get_created_files(self) -> ListBasedSet[str]:
        return ListBasedSet(os.listdir()) - self._preexisting_files

    def _create_issues_for_num_files(self):
        for requirement, output_files \
                in self.output_file_requirements.get_requirements_to_output_files(self.created_files).items():
            if len(output_files) < requirement.minimal_count:
                # The specified number of output files were not created.
                if requirement.is_wildcard():
                    issue = dedent_triple_quote_str(f"""
                        The code was supposed to create at least {requirement.minimal_count} files \
                        of "{requirement.filename}", \
                        but it only created {len(output_files)} files of this type.
                        """)
                else:
                    issue = f"The code didn't generate the desired output file, '{requirement.filename}'."
                self.issues.append(RunIssue(
                    category='Not all required files were created',
                    issue=issue,
                    code_problem=CodeProblem.MissingOutputFiles,
                    comment='Code did not create all required files'
                ))

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.created_files = self._get_created_files()
        if self.output_file_requirements is not None:
            self._create_issues_for_num_files()
            self.un_allowed_created_files = self.output_file_requirements.get_unmatched_files(self.created_files)
        else:
            self.un_allowed_created_files = []
        if self.un_allowed_created_files:
            raise UnAllowedFilesCreated(un_allowed_files=list(self.un_allowed_created_files))

        return super().__exit__(exc_type, exc_val, exc_tb)


@dataclass
class PreventImport(SingletonRegisteredRunContext):
    modules: Iterable[str] = None
    TEMPORARILY_DISABLE_IS_INTERNAL_ONLY = False

    _currently_importing: list = field(default_factory=list)

    def _reversible_enter(self):
        self.original_import = builtins.__import__
        builtins.__import__ = self.custom_import
        return super()._reversible_enter()

    def _reversible_exit(self):
        builtins.__import__ = self.original_import
        return super()._reversible_exit()

    def is_currently_importing(self) -> bool:
        return len(self._currently_importing) > 0

    def custom_import(self, name, globals=None, locals=None, fromlist=(), level=0):
        if self._is_called_from_user_script() and \
                (any(name.startswith(module + '.') for module in self.modules) or name in self.modules):
            raise CodeImportForbiddenModule(module=name)
        with self.within_import(name):
            try:
                return self.original_import(name, globals, locals, fromlist, level)
            except Exception as e:
                exc = ImportError(str(e))
                exc.fromlist = fromlist
                raise exc

    @contextmanager
    def within_import(self, package_name):
        """
        Context manager for tracking when we enter an import statement.
        """
        self._currently_importing.append(package_name)
        try:
            yield
        finally:
            self._currently_importing.pop()


@dataclass
class WarningHandler(SingletonRegisteredRunContext):
    categories_to_issue: Iterable[Type[Warning]] = field(default_factory=list)
    categories_to_raise: Iterable[Type[Warning]] = field(default_factory=list)
    categories_to_ignore: Iterable[Type[Warning]] = field(default_factory=list)
    TEMPORARILY_DISABLE_IS_INTERNAL_ONLY = False
    original_showwarning: Callable = None

    def _reversible_enter(self):
        self.original_showwarning = warnings.showwarning
        warnings.showwarning = self._warning_handler
        return super()._reversible_enter()

    def _reversible_exit(self):
        warnings.showwarning = self.original_showwarning
        return super()._reversible_exit()

    def _warning_handler(self, message, category, filename, lineno, file=None, line=None):
        if any(issubclass(category, cls) for cls in self.categories_to_issue):
            linenos_lines, _ = FailedRunningCode.from_current_tb().get_lineno_line_message()
            self.issues.append(RunIssue(
                issue=f'Code produced an undesired warning:\n```\n{str(message).strip()}\n```',
                code_problem=CodeProblem.NonBreakingRuntimeIssue,
                linenos_and_lines=linenos_lines,
            ))
        elif any(issubclass(category, cls) for cls in self.categories_to_raise):
            raise message
        elif any(issubclass(category, cls) for cls in self.categories_to_ignore):
            pass
        else:
            return self.original_showwarning(message, category, filename, lineno, file, line)
