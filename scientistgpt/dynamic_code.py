import os
import importlib
import traceback
import chatgpt_created_scripts

from scientistgpt.decorators import timeout
from scientistgpt.exceptions import FailedRunningCode

MODULE_NAME = "eval_script"
module_file = MODULE_NAME + ".py"
MAX_EXEC_TIME = 10  # seconds


chatgpt_created_scripts_dir = os.path.dirname(chatgpt_created_scripts.__file__)


def save_to_module_file(code: str):
    with open(os.path.join(chatgpt_created_scripts_dir, module_file), "w") as f:
        f.write(code)


# create a module that we can vary dynamically:
save_to_module_file('# empty module\n')
dynamic_module = importlib.import_module('chatgpt_created_scripts.' + MODULE_NAME)


@timeout(MAX_EXEC_TIME)
def run_code_from_file(code: str):
    """
    Run the provided code and terminate if runtime is too long.
    Raises a TimeoutError exception.

    To run the code, we save it to a .py file and ise the importlib to import it.
    """
    save_to_module_file(code)
    try:
        importlib.reload(dynamic_module)
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        raise FailedRunningCode(exception=e, tb=tb, code=code)
