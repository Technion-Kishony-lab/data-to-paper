import os
import time

import numpy as np

from typing import Dict, Union, List, Tuple

from data_to_paper.run_gpt_code.attr_replacers import AttrReplacer
from data_to_paper.run_gpt_code.overrides.pvalue import PValue, OnStrPValue, OnStr
from data_to_paper.run_gpt_code.run_issues import CodeProblem, RunIssue
from data_to_paper.utils.check_type import validate_value_type, WrongTypeException

BasicTypes = Union[str, int, float, bool, np.number, None, PValue]

AllowedType = Dict[str, Union[BasicTypes, Dict[str, BasicTypes], List[BasicTypes], Tuple[BasicTypes, ...]]]


def _pickle_dump_with_checks(obj, file, *args, original_func=None, context_manager: AttrReplacer = None, **kwargs):
    """
    Save a Dict[str, Any] to a pickle file.
    Check for content issues.
    """
    filename = file.name
    category = 'Use of `pickle.dump`'

    def close_and_remove_and_raise(e: Exception):
        file.close()
        time.sleep(0.1)
        os.remove(filename)  # the file is already open and has size 0
        raise e

    # Do not allow any other arguments
    if args or kwargs:
        close_and_remove_and_raise(RunIssue.from_current_tb(
            category=category,
            item=filename,
            issue="Please use `dump(obj, file)` with only the `obj` and `file` arguments.",
            instructions="Please do not specify any other arguments.",
            code_problem=CodeProblem.RuntimeError,
        ))

    # Only allow a dictionary with string keys and values that are basic types.
    if not isinstance(obj, dict) or not all(isinstance(key, str) for key in obj.keys()):
        close_and_remove_and_raise(RunIssue.from_current_tb(
            category=category,
            item=filename,
            issue="You can only save a dictionary with string keys and values that are basic types.",
            code_problem=CodeProblem.RuntimeError,
        ))

    try:
        validate_value_type(obj, AllowedType)
    except WrongTypeException as e:
        close_and_remove_and_raise(RunIssue.from_current_tb(
            category=category,
            item=filename,
            issue="You can only save a dictionary with string keys and values that are basic types.\n"
                  "Checking the type of the saved object, I found: " + e.get_found_description(),
            instructions=f"Please make sure that the object you are saving to the {filename} is a dictionary with "
                         f"string keys and simple-type values.",
            code_problem=CodeProblem.RuntimeError,
        ))

    # try str of the dict. This will raise an error if the dict contains object that
    #  we do not allow to show as text.
    try:
        with OnStrPValue(OnStr.SMALLER_THAN):
            s = str(obj)
    except Exception as e:
        close_and_remove_and_raise(RunIssue.from_current_tb(
            category=category,
            item=filename,
            issue="The saved dictionary contains objects that cannot be shown as text.\n"
                  "It created the following error:\n" + str(e),
            code_problem=CodeProblem.RuntimeError,
        ))

    if len(s) > 500:
        close_and_remove_and_raise(RunIssue.from_current_tb(
            category=category,
            item=filename,
            issue="The saved dictionary is too large to be shown as text.",
            instructions="Please reduce the amount of data you are saving to the file.",
            code_problem=CodeProblem.RuntimeError,
        ))

    with PValue.BEHAVE_NORMALLY.temporary_set(True):
        return original_func(obj, file)


def get_pickle_dump_attr_replacer():
    return AttrReplacer(obj_import_str='pickle', attr='dump', wrapper=_pickle_dump_with_checks,
                        send_context_to_wrapper=True, send_original_to_wrapper=True)
