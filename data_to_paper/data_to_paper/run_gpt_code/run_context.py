from __future__ import annotations

import builtins
import os
import traceback
import warnings

from contextlib import contextmanager, ExitStack
from dataclasses import dataclass, field
from typing import Tuple, Any, Iterable, Callable, List, Type, Dict, TypeVar, Optional

from data_to_paper.utils.file_utils import is_name_matches_list_of_wildcard_names
from data_to_paper.utils.types import ListBasedSet

from .exceptions import CodeUsesForbiddenFunctions, CodeWriteForbiddenFile, CodeReadForbiddenFile, \
    CodeImportForbiddenModule, UnAllowedFilesCreated
from .types import CodeProblem, RunIssue, module_filename, RunIssues

T = TypeVar('T', bound='BaseRunContext')


@dataclass
class BaseRunContext:
    calling_module_name = 'data-to-paper'
    PROCESS_AND_NAME_TO_OBJECT = {}
    _is_enabled: Optional[bool] = None  # None means that the context is not initialized yet

    issues: Optional[RunIssues] = None

    @property
    def _name(self) -> str:
        return self.__class__.__name__

    def __enter__(self):
        self._is_enabled = True
        self.issues = RunIssues()
        process_id = os.getpid()
        self.PROCESS_AND_NAME_TO_OBJECT[(process_id, self._name)] = self
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._is_enabled = None
        process_id = os.getpid()
        del self.PROCESS_AND_NAME_TO_OBJECT[(process_id, self._name)]
        return False  # do not suppress exceptions

    def _is_called_from_user_script(self) -> bool:
        """
        Check if the code is called from user script.
        """
        tb = traceback.extract_stack()
        filename = tb[-3].filename
        return filename.endswith(module_filename)

    def _is_called_from_data_to_paper(self) -> bool:
        tb = traceback.extract_stack()
        filename = tb[-3].filename
        return self.calling_module_name in filename

    @classmethod
    def get_runtime_instance(cls: Type[T]) -> T:
        process_id = os.getpid()
        if (process_id, cls.__name__) not in cls.PROCESS_AND_NAME_TO_OBJECT:
            raise RuntimeError(f'No runtime access was given to the code for {cls.__name__}.')
        return cls.PROCESS_AND_NAME_TO_OBJECT[(process_id, cls.__name__)]

    @classmethod
    @contextmanager
    def disable(cls):
        """
        Context manager for temporarily disabling the runtime context.
        """
        self = cls.get_runtime_instance()
        assert self._is_enabled is not None, 'The context is not initialized yet.'
        current_is_enabled = self._is_enabled
        self._is_enabled = False
        try:
            yield
        finally:
            self._is_enabled = current_is_enabled

    @classmethod
    def get_all_runtime_instances(cls) -> List[BaseRunContext]:
        process_id = os.getpid()
        return [obj for (pid, _), obj in cls.PROCESS_AND_NAME_TO_OBJECT.items() if pid == process_id]

    @staticmethod
    @contextmanager
    def disable_all():
        """
        Context manager for temporarily disabling all runtime contexts.
        """
        objs = BaseRunContext.get_all_runtime_instances()
        with ExitStack() as stack:
            for obj in objs:
                stack.enter_context(obj.disable())
            yield


@dataclass
class ProvideData(BaseRunContext):
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
class IssueCollector(BaseRunContext):
    pass


@dataclass
class PreventFileOpen(BaseRunContext):
    SYSTEM_FILES = ['templates/latex_table.tpl', 'templates/latex_longtable.tpl']
    SYSTEM_FOLDERS = \
        [r'C:\Windows', r'C:\Program Files', r'C:\Program Files (x86)'] if os.name == 'nt' \
        else ['/usr', '/etc', '/bin', '/sbin', '/sys', '/dev', '/var', '/opt', '/proc']

    allowed_read_files: Iterable[str] = None  # list of wildcard names,  None means allow all, [] means allow none
    allowed_write_files: Iterable[str] = None  # list of wildcard names,  None means allow all, [] means allow none

    original_open: Callable = None

    def __enter__(self):
        self.original_open = builtins.open
        builtins.open = self.open_wrapper
        return super().__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        builtins.open = self.original_open
        return super().__exit__(exc_type, exc_val, exc_tb)

    def is_allowed_read_file(self, file_name: str) -> bool:
        return self.allowed_read_files is None or \
            is_name_matches_list_of_wildcard_names(file_name, self.allowed_read_files) or \
            self._is_system_file(file_name)

    def is_allowed_write_file(self, file_name: str) -> bool:
        return self.allowed_write_files is None or \
            is_name_matches_list_of_wildcard_names(file_name, self.allowed_write_files)

    def open_wrapper(self, *args, **kwargs):
        if not self._is_enabled:
            return self.original_open(*args, **kwargs)
        file_name = args[0] if len(args) > 0 else kwargs.get('file', None)
        open_mode = args[1] if len(args) > 1 else kwargs.get('mode', 'r')
        is_opening_for_writing = open_mode in ['w', 'a', 'x']
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
class PreventCalling(BaseRunContext):
    modules_and_functions: Iterable[Tuple[Any, str, bool]] = None
    _original_functions: Dict[str, Callable] = None

    def __enter__(self):
        self._original_functions = {}
        for module, function_name, should_only_create_issue in self.modules_and_functions:
            original_func = getattr(module, function_name)
            setattr(module, function_name, self.get_upon_called(function_name, original_func, should_only_create_issue))
            self._original_functions[function_name] = original_func
        return super().__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        for module, function_name, _ in self.modules_and_functions:
            setattr(module, function_name, self._original_functions.pop(function_name))
        return super().__exit__(exc_type, exc_val, exc_tb)

    def get_upon_called(self, func_name: str, original_func: Callable, should_only_create_issue: bool):
        def upon_called(*args, **kwargs):
            if not self._is_enabled or not self._is_called_from_user_script():
                return original_func(*args, **kwargs)
            if should_only_create_issue:
                self.issues.append(RunIssue(
                    issue=f'Code uses forbidden function: "{func_name}".',
                    code_problem=CodeProblem.NonBreakingRuntimeIssue,
                ))
            else:
                raise CodeUsesForbiddenFunctions(func_name)
            return original_func(*args, **kwargs)
        return upon_called


@dataclass
class TrackCreatedFiles(BaseRunContext):
    allowed_create_files: Iterable[str] = None  # list of wildcard names,  None means allow all, [] means allow none

    created_files: ListBasedSet[str] = None
    un_allowed_created_files: List[str] = None

    def __enter__(self):
        self._preexisting_files = ListBasedSet(os.listdir())
        return super().__enter__()

    def _get_created_files(self) -> ListBasedSet[str]:
        return ListBasedSet(os.listdir()) - self._preexisting_files

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.created_files = self._get_created_files()
        self.un_allowed_created_files = []
        if self.allowed_create_files is not None:
            for file in self.created_files:
                if not is_name_matches_list_of_wildcard_names(file, self.allowed_create_files):
                    self.un_allowed_created_files.append(file)
        if self.un_allowed_created_files:
            raise UnAllowedFilesCreated(un_allowed_files=list(self.un_allowed_created_files))

        return super().__exit__(exc_type, exc_val, exc_tb)


@dataclass
class PreventImport(BaseRunContext):
    modules: Iterable[str] = None

    _currently_importing: list = field(default_factory=list)

    def __enter__(self):
        self.original_import = builtins.__import__
        builtins.__import__ = self.custom_import
        return super().__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        builtins.__import__ = self.original_import
        return super().__exit__(exc_type, exc_val, exc_tb)

    def is_currently_importing(self) -> bool:
        return len(self._currently_importing) > 0

    def custom_import(self, name, globals=None, locals=None, fromlist=(), level=0):
        if self._is_enabled and self._is_called_from_user_script() and \
                (any(name.startswith(module + '.') for module in self.modules) or name in self.modules):
            raise CodeImportForbiddenModule(module=name)
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
class WarningHandler(BaseRunContext):
    categories_to_issue: Iterable[Type[Warning]] = field(default_factory=list)
    categories_to_raise: Iterable[Type[Warning]] = field(default_factory=list)
    categories_to_ignore: Iterable[Type[Warning]] = field(default_factory=list)

    original_showwarning: Callable = None

    def __enter__(self):
        self.original_showwarning = warnings.showwarning
        warnings.showwarning = self._warning_handler
        return super().__enter__()

    def __exit__(self, exc_type, exc_value, traceback):
        warnings.showwarning = self.original_showwarning
        return super().__exit__(exc_type, exc_value, traceback)

    def _warning_handler(self, message, category, filename, lineno, file=None, line=None):
        if not self._is_enabled:
            return self.original_showwarning(message, category, filename, lineno, file, line)
        if any(issubclass(category, cls) for cls in self.categories_to_issue):
            self.issues.append(RunIssue(
                issue=f'Code produced an undesired warning:\n```\n{str(message).strip()}\n```',
                code_problem=CodeProblem.NonBreakingRuntimeIssue,
            ))
        elif any(issubclass(category, cls) for cls in self.categories_to_raise):
            raise message
        elif any(issubclass(category, cls) for cls in self.categories_to_ignore):
            pass
        else:
            return self.original_showwarning(message, category, filename, lineno, file, line)
