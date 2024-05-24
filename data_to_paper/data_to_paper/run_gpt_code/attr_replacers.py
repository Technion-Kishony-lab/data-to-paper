from __future__ import annotations

import importlib
import pkgutil
from dataclasses import dataclass

import inspect

from typing import Callable, Iterable, Any, Optional, Tuple, Dict, Union

from .base_run_contexts import RegisteredRunContext
from .exceptions import CodeUsesForbiddenFunctions
from .run_issues import CodeProblem, RunIssue


def _carefully_get_members(module):
    try:
        return inspect.getmembers(module)
    except Exception:
        return []


def get_all_submodules(module, visited=None):
    """Recursively get all sub-modules of a module, avoiding loops."""
    if visited is None:
        visited = set()

    all_submodules = []

    for name, obj in _carefully_get_members(module):
        if inspect.ismodule(obj) and obj not in visited:
            visited.add(obj)
            all_submodules.append(obj)
            all_submodules.extend(get_all_submodules(obj, visited))

    return all_submodules


def import_submodules(package):
    """ Recursively import all submodules of a module, including sub-packages """
    if isinstance(package, str):
        package = importlib.import_module(package)
    results = {}
    for loader, name, is_pkg in pkgutil.walk_packages(package.__path__):
        full_name = package.__name__ + '.' + name
        try:
            results[full_name] = importlib.import_module(full_name)
            if is_pkg:
                results.update(import_submodules(full_name))
        except ModuleNotFoundError:
            continue
    return results


def dynamic_import(full_path):
    """Dynamically import a module or class from a string path."""
    try:
        # This will work if the path is to a module (e.g., 'statsmodels.stats.multitest')
        return importlib.import_module(full_path)
    except ImportError:
        # If direct import fails, it might be a class or function in a module
        module_path, class_or_func_name = full_path.rsplit('.', 1)
        module = importlib.import_module(module_path)
        return getattr(module, class_or_func_name)


def _import_obj(obj_import_str: Optional[str, Any]):
    if obj_import_str is None:
        return None
    if isinstance(obj_import_str, str):
        return dynamic_import(obj_import_str)
    return obj_import_str


@dataclass
class OverrideImportedObjContext(RegisteredRunContext):
    TEMPORARILY_DISABLE_IS_INTERNAL_ONLY = True
    obj_import_str: Optional[str, Any] = None

    @property
    def obj(self):
        return _import_obj(self.obj_import_str)


@dataclass
class MultiAttrReplacerContext(OverrideImportedObjContext):
    _originals: Optional[dict] = None

    def _get_all_parents(self) -> set:
        raise NotImplementedError

    def _get_all_attrs_for_parent(self, parent) -> Iterable[str]:
        raise NotImplementedError

    def _get_custom_wrapper(self, parent, attr_name, original_func):
        raise NotImplementedError

    def __enter__(self):
        self._originals = {}
        for parent in self._get_all_parents():
            for attr_name in self._get_all_attrs_for_parent(parent):
                original = getattr(parent, attr_name)
                self._originals[(parent, attr_name)] = original
                setattr(parent, attr_name, self._get_custom_wrapper(parent, attr_name, original))
        return super().__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        for (parent, attr_name), original in self._originals.items():
            setattr(parent, attr_name, original)
        self._originals = None
        return super().__exit__(exc_type, exc_val, exc_tb)


@dataclass
class SystematicAttrReplacerContext(MultiAttrReplacerContext):
    recursive: bool = True

    def _get_all_modules(self) -> list:
        all_modules = [self.obj]
        if self.recursive:
            all_modules += get_all_submodules(self.obj)
        return all_modules

    def _is_right_type(self, obj) -> bool:
        return NotImplemented

    def _should_replace(self, parent, attr_name, attr) -> bool:
        return NotImplemented

    def _get_all_attrs_for_parent(self, parent) -> Iterable[str]:
        return [attr_name for attr_name, attr_obj in parent.__dict__.items()
                if self._is_right_type(attr_obj) and self._should_replace(parent, attr_name, attr_obj)]


class SystematicMethodReplacerContext(SystematicAttrReplacerContext):
    def _get_all_parents(self) -> list:
        classes = []
        for mod in self._get_all_modules():
            for name, obj in _carefully_get_members(mod):
                if inspect.isclass(obj) and obj not in classes:
                    classes.append(obj)
        return classes

    def _is_right_type(self, obj) -> bool:
        return inspect.isfunction(obj) or inspect.ismethod(obj)


class SystematicFuncReplacerContext(SystematicAttrReplacerContext):
    def _get_all_parents(self) -> list:
        return self._get_all_modules()

    def _is_right_type(self, obj) -> bool:
        return inspect.isfunction(obj)


@dataclass
class AttrReplacer(OverrideImportedObjContext):
    attr: str = None
    wrapper: Union[Callable, Any] = None

    send_context_to_wrapper: bool = False
    send_original_to_wrapper: bool = False

    _original: Callable = None

    def _get_wrapper(self):
        return self.wrapper

    def _get_wrapped_wrapper(self):
        if not callable(self._get_wrapper()):
            return self._get_wrapper()

        def wrapped_wrapper(*args, **kwargs):
            if not self._is_enabled or not self._is_called_from_data_to_paper():
                return self._original(*args, **kwargs)
            if self.send_context_to_wrapper:
                kwargs['context_manager'] = self
            if self.send_original_to_wrapper:
                kwargs['original_func'] = self._original
            return self._get_wrapper()(*args, **kwargs)
        return wrapped_wrapper

    def _reversible_enter(self):
        self._original = getattr(self.obj, self.attr)
        setattr(self.obj, self.attr, self._get_wrapped_wrapper())

    def _reversible_exit(self):
        setattr(self.obj, self.attr, self._original)


@dataclass
class PreventAssignmentToAttrs(OverrideImportedObjContext):
    forbidden_set_attrs: Iterable[str] = ()
    message: str = 'Cannot set {attr}.'
    _original: Callable = None

    def _get_wrapper(self):
        def _replacement__setattr__(obj, attr, value):
            if not self._is_enabled or not self._is_called_from_user_script():
                return self._original(obj, attr, value)
            if attr in self.forbidden_set_attrs:
                self._raise_exception(attr, value)
            return self._original(obj, attr, value)
        return _replacement__setattr__

    def _raise_exception(self, attr, value):
        raise AttributeError(self.message.format(attr=attr))

    def _reversible_enter(self):
        self._original = self.obj.__setattr__
        self.obj.__setattr__ = self._get_wrapper()

    def _reversible_exit(self):
        self.obj.__setattr__ = self._original


@dataclass
class PreventCalling(RegisteredRunContext):
    TEMPORARILY_DISABLE_IS_INTERNAL_ONLY = True
    modules_and_functions: Iterable[Tuple[Any, str, bool]] = None
    _original_functions: Optional[Dict[str, Callable]] = None

    def __enter__(self):
        self._original_functions = {}
        for module, function_name, should_only_create_issue in self.modules_and_functions:
            module = _import_obj(module)
            original_func = getattr(module, function_name)
            setattr(module, function_name, self.get_upon_called(function_name, original_func, should_only_create_issue))
            self._original_functions[function_name] = original_func
        return super().__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        for module, function_name, _ in self.modules_and_functions:
            module = _import_obj(module)
            setattr(module, function_name, self._original_functions.pop(function_name))
        self._original_functions = None
        return super().__exit__(exc_type, exc_val, exc_tb)

    def get_upon_called(self, func_name: str, original_func: Callable, should_only_create_issue: bool):
        def upon_called(*args, **kwargs):
            if not self._is_enabled or not self._is_called_from_user_script():
                return original_func(*args, **kwargs)
            if should_only_create_issue:
                self.issues.append(RunIssue.from_current_tb(
                    category='Coding: good practices',
                    issue=f'Code uses forbidden function: "{func_name}".',
                    code_problem=CodeProblem.NonBreakingRuntimeIssue,
                ))
            else:
                raise CodeUsesForbiddenFunctions(func_name)
            return original_func(*args, **kwargs)
        return upon_called
