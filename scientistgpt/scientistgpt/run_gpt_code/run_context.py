import builtins
import os
import traceback
from contextlib import contextmanager
from typing import Tuple, Any, Iterable

from scientistgpt.run_gpt_code.exceptions import CodeUsesForbiddenFunctions, \
    CodeWriteForbiddenFile, CodeReadForbiddenFile, CodeImportForbiddenModule
from scientistgpt.utils.file_utils import is_name_matches_list_of_wildcard_names


IMPORTING_PACKAGES = []
if os.name == 'nt':
    SYSTEM_FOLDERS = [r'C:\Windows', r'C:\Program Files', r'C:\Program Files (x86)']
else:
    SYSTEM_FOLDERS = ['/usr', '/etc', '/bin', '/sbin', '/sys', '/dev', '/var', '/opt', '/proc']


@contextmanager
def prevent_file_open(allowed_read_files: Iterable[str] = None, allowed_write_files: Iterable[str] = None):
    """
    Context manager for restricting the code from opening un-allowed files.

    allowed_read_files: list of files that the code is allowed to read from. If None, all files are allowed.
    allowed_write_files: list of files that the code is allowed to write to. If None, all files are allowed.
        can also be a wildcard filename, e.g. '*.csv'.
    """

    original_open = builtins.open

    def open_wrapper(*args, **kwargs):
        file_name = args[0] if len(args) > 0 else kwargs.get('file', None)
        open_mode = args[1] if len(args) > 1 else kwargs.get('mode', 'r')
        is_opening_for_writing = open_mode in ['w', 'a', 'x']
        if is_opening_for_writing and allowed_write_files is not None \
                and not is_name_matches_list_of_wildcard_names(file_name, allowed_write_files):
            raise CodeWriteForbiddenFile(file=file_name)
        if not is_opening_for_writing and not file_in_system_folder(file_name) and \
                (allowed_read_files is not None and file_name not in allowed_read_files
                 and len(IMPORTING_PACKAGES) == 0):  # allow read files when importing packages
            raise CodeReadForbiddenFile(file=file_name)
        return original_open(*args, **kwargs)

    builtins.open = open_wrapper
    try:
        yield
    finally:
        builtins.open = original_open

def file_in_system_folder(file_name):
    abs_path_to_file = os.path.abspath(file_name)
    return bool(sum([os.path.commonpath([folder] + [abs_path_to_file]) in SYSTEM_FOLDERS for folder in SYSTEM_FOLDERS]))

@contextmanager
def prevent_calling(modules_and_functions: Iterable[Tuple[Any, str]] = None):
    """
    Context manager for catching when the code tries to use certain forbidden functions.

    modules_and_functions: list of tuples of (module, function_name) that the code is not allowed to call.
    """
    modules_and_functions = modules_and_functions or []

    def get_upon_called(func_name, original_func):
        from scientistgpt.run_gpt_code.dynamic_code import module_filename

        def upon_called(*args, **kwargs):
            # We check that the function was called from the module we are running
            # (functions like print are also called from pytest)
            frame = traceback.extract_stack()[-2]
            if frame.filename.endswith(module_filename):
                raise CodeUsesForbiddenFunctions(func_name)
            return original_func(*args, **kwargs)
        return upon_called

    original_functions = []

    for module, function_name in modules_and_functions:
        original_function = getattr(module, function_name)
        original_functions.append(original_function)
        setattr(module, function_name, get_upon_called(function_name, original_function))

    try:
        yield
    finally:
        # we restore the original functions
        for module, function_name in modules_and_functions:
            setattr(module, function_name, original_functions.pop(0))


@contextmanager
def within_import(package_name):
    """
    Context manager for tracking when we enter an import statement.
    """
    IMPORTING_PACKAGES.append(package_name)
    try:
        yield
    finally:
        IMPORTING_PACKAGES.pop()


class PreventImport:
    def __init__(self, modules):
        from scientistgpt.run_gpt_code.dynamic_code import module_filename
        self.modules = modules
        self.module_filename = module_filename

    def __enter__(self):
        self.original_import = builtins.__import__
        builtins.__import__ = self.custom_import
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        builtins.__import__ = self.original_import

    def custom_import(self, name, *args, **kwargs):
        if any(name.startswith(module + '.') for module in self.modules) or name in self.modules:
            frame = traceback.extract_stack()[-2]
            if frame.filename.endswith(self.module_filename):
                raise CodeImportForbiddenModule(module=name)
        with within_import(name):
            return self.original_import(name, *args, **kwargs)
