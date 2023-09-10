from data_to_paper.run_gpt_code.overrides.types import is_p_value, PValue
from data_to_paper.run_gpt_code.types import CodeProblem, RunIssue, RunUtilsError
from data_to_paper.env import TRACK_P_VALUES

from ..original_utils import format_p_value


def _format_p_value(x):
    """
    Replacement of format_p_value tp be used by ChatGPT code.
    Same as format_p_value, but also checks that the input is a PValue object.
    """
    if TRACK_P_VALUES:
        _check_argument_for_format_p_value(x)
        return format_p_value(x.value if is_p_value(x) else x)
    else:
        return format_p_value(x)


def _check_argument_for_format_p_value(x):
    if isinstance(x, str) and (x == '-' or x == 'NA'):
        return

    if not is_p_value(x) and not isinstance(x, float):
        with PValue.allow_str.temporary_set(True):
            raise ValueError(f"format_p_value should only be applied to P-value float.\n"
                             f"But got type: {type(x)}, value: {repr(x)}.")
    if not is_p_value(x):
        raise RunUtilsError(
            RunIssue(
                code_problem=CodeProblem.RuntimeError,
                issue=f"It seems like you are applying format_p_value to some values that are not P-Values.",
                instructions=f"You should only apply format_p_value to P-Values.",
            )
        )


def is_ok_to_apply_format_p_value(x):
    try:
        _check_argument_for_format_p_value(x)
        return True
    except (RunUtilsError, ValueError):
        return False
