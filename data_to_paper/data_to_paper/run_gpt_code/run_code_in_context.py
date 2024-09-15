from types import ModuleType
from typing import Callable, Union, Tuple, Any, Optional

from .base_run_contexts import MultiRunContext
from .exceptions import FailedRunningCode

from data_to_paper.utils.types import ListBasedSet
from data_to_paper.base_steps import BaseCodeProductsGPT


def run_code_in_context(code: Union[str, Callable, ModuleType], code_converser: BaseCodeProductsGPT,
                        run_folder: str = None
                        ) -> Tuple[Any, ListBasedSet[str], MultiRunContext, Optional[FailedRunningCode]]:
    """
    This function allows to manually run code created by the LLM model.
    We provide the code to run and the code_converser object that was used to create the code.
    The code is run in the correct context and the result is returned.

    The `code` can be provided as:
    - a string of code
        To run the code, we save it to a .py file and use the importlib to import it.
    - a function
        The function is called in the current context.
    - a module
        The module is reloaded and the function is called in the current context.

    run_folder:
        The folder where the code will be run (where the data is stored).
        If not provided, the code will run in the default run_folder (FOLDER_FOR_RUN).
    """
    debugger = code_converser.get_debugger(
        data_filenames='all',  # do not limit the data files
        data_folder=run_folder,
        is_new_conversation=None,
    )
    code_runner = debugger.get_code_runner()
    if run_folder is not None:
        code_runner.run_folder = run_folder
    return code_runner.run(code)
