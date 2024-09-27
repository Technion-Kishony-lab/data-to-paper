from __future__ import annotations

import builtins
import os
import tempfile
import warnings

from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Iterable, Callable, List, Type, Dict, Optional, Union, Tuple, NamedTuple

from pathlib import Path

from data_to_paper.utils.file_utils import is_name_matches_list_of_wildcard_names
from data_to_paper.utils.types import ListBasedSet
from data_to_paper.text import dedent_triple_quote_str

from .exceptions import CodeWriteForbiddenFile, CodeReadForbiddenFile, \
    CodeImportForbiddenModule, UnAllowedFilesCreated
from .run_issues import CodeProblem, RunIssue
from data_to_paper.code_and_output_files.output_file_requirements import OutputFileRequirements
from .base_run_contexts import SingletonRegisteredRunContext


@dataclass
class ProvideData(SingletonRegisteredRunContext):
    data: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def get_item(cls, key: str) -> Any:
        self = cls.get_runtime_instance()
        return self.data[key]


@dataclass
class IssueCollector(SingletonRegisteredRunContext):
    pass


def _is_temp_file(file_name):
    return file_name.startswith(tempfile.gettempdir())


@dataclass
class PreventFileOpen(SingletonRegisteredRunContext):
    SYSTEM_FILES = ['templates/latex_table.tpl', 'templates/latex_longtable.tpl', 'ttf/DejaVuSans.ttf',
                    'LICENSE.txt', 'LICENSE', 'LICENSE.md']
    SYSTEM_FOLDERS = \
        [r'C:\Windows', r'C:\Program Files', r'C:\Program Files (x86)'] if os.name == 'nt' \
        else ['/usr', '/etc', '/bin', '/sbin', '/sys', '/dev', '/var', '/opt', '/proc']
    allowed_read_files: Iterable[str] = 'all'  # list of wildcard names,  'all' means allow all, [] means allow none
    allowed_write_files: Iterable[str] = 'all'  # list of wildcard names,  'all' means allow all, [] means allow none
    allowed_write_folder: Optional[str] = None
    original_open: Optional[Callable] = None

    def _reversible_enter(self):
        self.original_open = builtins.open
        builtins.open = self.open_wrapper
        return super()._reversible_enter()

    def _reversible_exit(self):
        builtins.open = self.original_open
        self.original_open = None
        return super()._reversible_exit()

    def is_allowed_read_file(self, file_name: str) -> bool:
        return self.allowed_read_files == 'all' or \
            is_name_matches_list_of_wildcard_names(file_name, self.allowed_read_files) or \
            self._is_system_file(file_name)

    def is_allowed_write_file(self, file_name: str) -> bool:
        try:
            file_path = Path(file_name).resolve()
        except TypeError:
            return True
        if self.allowed_write_folder is not None and \
                file_path.parents[0].resolve() != Path(self.allowed_write_folder).resolve() and \
                not _is_temp_file(file_name):
            return False
        return self.allowed_write_files == 'all' or \
            is_name_matches_list_of_wildcard_names(file_path.name, self.allowed_write_files) or _is_temp_file(file_name)

    def open_wrapper(self, *args, **kwargs):
        file_name = args[0] if len(args) > 0 else kwargs.get('file', None)
        open_mode = args[1] if len(args) > 1 else kwargs.get('mode', 'r')
        is_opening_for_writing = open_mode in ['w', 'a', 'x', 'w+b', 'a+b', 'x+b', 'wb', 'ab', 'xb']
        # allow read/write files when importing packages
        if not ModifyImport.get_runtime_instance().is_currently_importing():
            if is_opening_for_writing:
                if not self.is_allowed_write_file(file_name):
                    raise CodeWriteForbiddenFile(file=file_name)
            else:
                if not self.is_allowed_read_file(file_name):
                    raise CodeReadForbiddenFile(file=file_name)
        return self.original_open(*args, **kwargs)

    def _is_system_file(self, file_name):
        abs_path_to_file = os.path.abspath(file_name)
        return any(abs_path_to_file.startswith(folder) for folder in self.SYSTEM_FOLDERS) or \
            any(abs_path_to_file.endswith(file) for file in self.SYSTEM_FILES)


class FileAndMetadata(NamedTuple):
    file: str
    metadata: Any


@dataclass
class TrackCreatedFiles(SingletonRegisteredRunContext):
    output_file_requirements: Optional[OutputFileRequirements] = None  # None means allow all

    created_files: Optional[ListBasedSet[str]] = None  # None - unknown, context is not yet exited
    un_allowed_created_files: Optional[List[str]] = None  # None - unknown, context is not yet exited
    _preexisting_files_and_metadata: ListBasedSet[FileAndMetadata] = None

    def _get_dir_files_and_metadata(self) -> ListBasedSet[FileAndMetadata]:
        return ListBasedSet((file, os.stat(file).st_mtime) for file in os.listdir())

    def __enter__(self):
        self._preexisting_files_and_metadata = self._get_dir_files_and_metadata()
        self.created_files = None
        self.un_allowed_created_files = None
        return super().__enter__()

    def _get_created_files(self) -> ListBasedSet[str]:
        files_and_metadata = self._get_dir_files_and_metadata() - self._preexisting_files_and_metadata
        return ListBasedSet(file for file, _ in files_and_metadata)

    def _create_issues_for_num_files(self):
        for requirement, output_files \
                in self.output_file_requirements.get_requirements_to_output_files(self.created_files).items():
            if len(output_files) < requirement.minimal_count:
                # The specified number of output files were not created.
                if requirement.is_wildcard():
                    issue = dedent_triple_quote_str(f"""
                        The code was supposed to create at least {requirement.minimal_count} files \t
                        of "{requirement.generic_filename}", \t
                        but it only created {len(output_files)} files of this type.
                        """)
                else:
                    issue = f"The code didn't generate the desired output file, '{requirement.generic_filename}'."
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
class ModifyImport(SingletonRegisteredRunContext):
    modified_imports: Iterable[Tuple[str, Optional[str]]] = field(default_factory=list)

    _currently_importing: list = field(default_factory=list)
    original_import: Optional[Callable] = None

    def __enter__(self):
        self._currently_importing = []
        return super().__enter__()

    def _reversible_enter(self):
        self.original_import = builtins.__import__
        builtins.__import__ = self.custom_import
        super()._reversible_enter()

    def _reversible_exit(self):
        builtins.__import__ = self.original_import
        self.original_import = None
        super()._reversible_exit()

    def is_currently_importing(self) -> bool:
        return len(self._currently_importing) > 0

    def custom_import(self, name, globals=None, locals=None, fromlist=(), level=0):
        if self._is_called_from_user_script():
            matched_module, new_name = \
                next(((module, new_name) for module, new_name in self.modified_imports
                      if name.startswith(module)), (None, None))
            if matched_module:
                if new_name is None:
                    raise CodeImportForbiddenModule(module=name)
                name = new_name + name[len(matched_module):]
        with self.within_import(name):
            try:
                return self.original_import(name, globals, locals, fromlist, level)
            except Exception as e:
                e.fromlist = fromlist
                raise e

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
    categories_to_issue: Optional[Iterable[Type[Warning]]] = ()
    categories_to_raise: Optional[Iterable[Type[Warning]]] = ()
    categories_to_ignore: Optional[Iterable[Type[Warning]]] = ()
    original_showwarning: Optional[Callable] = None

    def _reversible_enter(self):
        self.original_showwarning = warnings.showwarning
        warnings.showwarning = self._warning_handler
        super()._reversible_enter()

    def _reversible_exit(self):
        warnings.showwarning = self.original_showwarning
        self.original_showwarning = None
        super()._reversible_exit()

    @staticmethod
    def _is_matched_cls(category, classes):
        return classes is ... or any(issubclass(category, cls) for cls in classes)

    def _warning_handler(self, message, category, filename, lineno, file=None, line=None):
        if self._is_matched_cls(category, self.categories_to_raise):
            raise message
        elif self._is_matched_cls(category, self.categories_to_ignore):
            pass
        elif self._is_matched_cls(category, self.categories_to_issue):
            self.issues.append(RunIssue.from_current_tb(
                category='Undesired warning',
                issue=f'Code produced an undesired warning:\n```\n{str(message).strip()}\n```',
                instructions='Please see if you understand the cause of this warning and fix the code.\n'
                             'Alternatively, if the warning is expected, then change the code to ignore it.',
                code_problem=CodeProblem.NonBreakingRuntimeIssue,
            ))
        else:
            return self.original_showwarning(message, category, filename, lineno, file, line)


@dataclass
class RunInDirectory(SingletonRegisteredRunContext):
    """
    Run code in a specific folder.
    If folder is None, run in the current folder.
    """
    folder: Union[Path, str] = None
    original_cwd: Optional[str] = None

    def __enter__(self):
        self.original_cwd = os.getcwd()
        if self.folder is not None:
            os.chdir(self.folder)
        return super().__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.chdir(self.original_cwd)
        self.original_cwd = None
        return super().__exit__(exc_type, exc_val, exc_tb)
