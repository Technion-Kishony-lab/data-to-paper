from typing import Callable

import inspect
from contextlib import contextmanager


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


@contextmanager
def method_replacer(module, custom_func_wrapper: Callable, should_replace_func: Callable, recursive: bool = True):
    """
    Replace specific methods in a module and all its submodules with a custom wrapper function.
    `custom_func_wrapper` should be a function that takes the original function as its only argument.
    `should_replace_func` should be a function that takes the class and attribute name of the function
    and returns True if the function should be replaced.
    `recursive` determines whether to replace functions in submodules as well.
    """
    originals = {}

    all_modules = [module]
    if recursive:
        all_modules += get_all_submodules(module)

    visited_classes = set()
    for mod in all_modules:
        for name, obj in _carefully_get_members(mod):
            if inspect.isclass(obj) and obj not in visited_classes:
                visited_classes.add(obj)
                for attr_name, attr_obj in _carefully_get_members(obj):
                    if attr_name in obj.__dict__ and inspect.isfunction(attr_obj) \
                            and should_replace_func(obj, attr_name):
                        original_func = getattr(obj, attr_name)
                        assert not getattr(original_func, 'is_wrapped', False)
                        originals[(obj, attr_name)] = original_func
                        setattr(obj, attr_name, custom_func_wrapper(original_func))
    try:
        yield
    finally:
        for (obj, attr_name), original_func in originals.items():
            setattr(obj, attr_name, original_func)


@contextmanager
def func_replacer(module, custom_func_wrapper: Callable, should_replace_func: Callable, recursive: bool = True):
    """
    Replace specific funcs in a module and all its submodules with a custom wrapper function.
    `custom_func_wrapper` should be a function that takes the original function as its only argument.
    `should_replace_func` should be a function that takes the class and attribute name of the function
    and returns True if the function should be replaced.
    `recursive` determines whether to replace functions in submodules as well.
    """
    originals = {}

    all_modules = [module]
    if recursive:
        all_modules += get_all_submodules(module)

    for mod in all_modules:
        for func_name, func in _carefully_get_members(mod):
            if inspect.isfunction(func) and should_replace_func(mod, func_name):
                if getattr(func, 'is_wrapped', False):
                    continue
                originals[(mod, func_name)] = func
                setattr(mod, func_name, custom_func_wrapper(func))
    try:
        yield
    finally:
        for (mod, func_name), original_func in originals.items():
            setattr(mod, func_name, original_func)
