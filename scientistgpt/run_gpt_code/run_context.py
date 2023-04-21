from contextlib import contextmanager
from typing import List, Tuple, Any

from scientistgpt.run_gpt_code.exceptions import CodeUsesForbiddenFunctions


@contextmanager
def prevent_calling(modules_and_functions: List[Tuple[Any, str]] = None):
    """
    Context manager for catching when the code tries to open file and then checking that the file name is allowed.
    """
    modules_and_functions = modules_and_functions or []

    def get_upon_raise_function(func_name):
        def upon_raise(*args, **kwargs):
            raise CodeUsesForbiddenFunctions(func_name)
        return upon_raise

    original_functions = []

    for module, function_name in modules_and_functions:
        original_functions.append(getattr(module, function_name))
        setattr(module, function_name, get_upon_raise_function(function_name))

    try:
        yield
    finally:
        # we restore the original functions
        for module, function_name in modules_and_functions:
            setattr(module, function_name, original_functions.pop(0))



