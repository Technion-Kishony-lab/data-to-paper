import os

from data_to_paper.run_gpt_code.attr_replacers import AttrReplacer
from data_to_paper.run_gpt_code.overrides.pvalue import PValue, OnStrPValue, OnStr
from data_to_paper.run_gpt_code.run_contexts import PreventFileOpen
from data_to_paper.run_gpt_code.run_issues import CodeProblem, RunIssue


def _pickle_dump_with_checks(obj, file, *args, original_func=None, context_manager: AttrReplacer = None, **kwargs):
    """
    Save a Dict[str, Any] to a pickle file.
    Check for content issues.
    """
    filename = file.name
    category = 'Use of `pickle.dump`'

    # Do not allow any other arguments
    if args or kwargs:
        os.remove(filename)
        raise RunIssue.from_current_tb(
            category=category,
            item=filename,
            issue="Please use `dump(obj, file)` with only the `obj` and `file` arguments.",
            instructions="Please do not specify any other arguments.",
            code_problem=CodeProblem.RuntimeError,
        )

    # Only allow a dictionary with string keys:
    if not isinstance(obj, dict) or not all(isinstance(key, str) for key in obj.keys()):
        context_manager.issues.append(RunIssue.from_current_tb(
            category=category,
            item=filename,
            issue="Please use `dump(obj, filename)` with a dictionary `obj` with string keys.",
            code_problem=CodeProblem.RuntimeError,
        ))

    # try str of the dict. This will raise an error if the dict contains object that
    #  we do not allow to show as text.
    try:
        with OnStrPValue(OnStr.SMALLER_THAN):
            str(obj)
    except Exception as e:
        os.remove(filename)
        raise RunIssue.from_current_tb(
            category=category,
            item=filename,
            issue="The saved dictionary contains objects that cannot be shown as text.\n"
                  "It created the following error:\n" + str(e),
            code_problem=CodeProblem.RuntimeError,
        )

    with PValue.BEHAVE_NORMALLY.temporary_set(True):
        original_func(obj, file)


def get_pickle_dump_attr_replacer():
    return AttrReplacer(obj_import_str='pickle', attr='dump', wrapper=_pickle_dump_with_checks,
                        send_context_to_wrapper=True, send_original_to_wrapper=True)
