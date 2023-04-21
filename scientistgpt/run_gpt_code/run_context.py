from contextlib import contextmanager
from typing import List, Tuple, Any

from scientistgpt.run_gpt_code.exceptions import CodeUsesForbiddenFunctions


@contextmanager
def prevent_calling(modules_and_functions: List[Tuple[Any, str]] = None):
    """
    Context manager for catching when the code tries to open file and then checking that the file name is allowed.
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



