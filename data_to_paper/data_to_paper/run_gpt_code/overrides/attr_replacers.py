from __future__ import annotations

from dataclasses import dataclass, field

import inspect
from types import ModuleType
from typing import Callable, Union, Type, Iterable

from data_to_paper.run_gpt_code.base_run_contexts import RunContext, RegisteredRunContext


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


@dataclass
class SystematicAttrReplacerContext(RunContext):
    TEMPORARILY_DISABLE_IS_INTERNAL_ONLY = True
    base_module: object = None
    recursive: bool = True

    _originals: dict = None

    def _get_all_modules(self) -> list:
        all_modules = [self.base_module]
        if self.recursive:
            all_modules += get_all_submodules(self.base_module)
        return all_modules

    def _get_all_parents(self) -> set:
        return NotImplemented

    def _is_right_type(self, obj) -> bool:
        return NotImplemented

    def _should_replace(self, parent, attr_name, attr) -> bool:
        return NotImplemented

    def _get_custom_wrapper(self, parent, attr_name, original_func):
        return NotImplemented

    def __enter__(self):
        self._originals = {}

        for parent in self._get_all_parents():
            for attr_name, attr_obj in parent.__dict__.items():
                if (parent, attr_name) not in self._originals \
                        and self._is_right_type(attr_obj) \
                        and self._should_replace(parent, attr_name, attr_obj):
                    original = getattr(parent, attr_name)
                    assert original is attr_obj
                    self._originals[(parent, attr_name)] = original
                    setattr(parent, attr_name, self._get_custom_wrapper(parent, attr_name, original))

    def __exit__(self, exc_type, exc_val, exc_tb):
        for (parent, attr_name), original in self._originals.items():
            setattr(parent, attr_name, original)


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
class AttrReplacer(RegisteredRunContext):
    TEMPORARILY_DISABLE_IS_INTERNAL_ONLY = True

    attr: str = None
    cls: Union[Type, ModuleType] = None
    wrapper: Callable = None

    send_context_to_wrapper: bool = False
    send_original_to_wrapper: bool = False

    _original: Callable = None

    def _get_wrapper(self):
        return self.wrapper

    def _get_wrapped_wrapper(self):
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
        self._original = getattr(self.cls, self.attr)
        setattr(self.cls, self.attr, self._get_wrapped_wrapper())

    def _reversible_exit(self):
        setattr(self.cls, self.attr, self._original)


@dataclass
class PreventAssignmentToAttrs(RegisteredRunContext):
    TEMPORARILY_DISABLE_IS_INTERNAL_ONLY = True
    cls: Type = None
    forbidden_set_attrs: Iterable[str] = field(default_factory=list)
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
        self._original = self.cls.__setattr__
        self.cls.__setattr__ = self._get_wrapper()

    def _reversible_exit(self):
        self.cls.__setattr__ = self._original
