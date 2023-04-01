import os
import importlib
import traceback
import chatgpt_created_scripts

from scientistgpt.decorators import timeout
from scientistgpt.exceptions import FailedRunningCode

MODULE_NAMES_TO_MODULES = {}
MAX_EXEC_TIME = 10  # seconds


def save_code_to_module_file(code: str, module_name: str):
    module_dir = os.path.dirname(chatgpt_created_scripts.__file__)
    with open(os.path.join(module_dir, module_name) + ".py", "w") as f:
        f.write(code)


@timeout(MAX_EXEC_TIME)
def run_code_from_file(code: str, module_name: str):
    """
    Run the provided code by saving to a file and importing.

    Raises a TimeoutError exception if runs too long.

    To run the code, we save it to a .py file and use the importlib to import it.
    If the file was already imported before, we use importlib.reload.
    """

    save_code_to_module_file(code, module_name)
    try:
        if module_name in MODULE_NAMES_TO_MODULES:
            # File was already imported. Need to reload:
            module = MODULE_NAMES_TO_MODULES[module_name]
            importlib.reload(module)
        else:
            # Importing a new module:
            module = importlib.import_module(chatgpt_created_scripts.__name__ + '.' + module_name)
            MODULE_NAMES_TO_MODULES[module_name] = module
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        raise FailedRunningCode(exception=e, tb=tb, code=code)
