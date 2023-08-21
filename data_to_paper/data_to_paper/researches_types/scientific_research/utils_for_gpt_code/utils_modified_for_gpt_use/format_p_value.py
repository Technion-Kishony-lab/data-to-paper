from data_to_paper.run_gpt_code.overrides.types import PValue
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
        return format_p_value(x.value)
    else:
        return format_p_value(x)


def _check_argument_for_format_p_value(x):
    if not isinstance(x, PValue) and not isinstance(x, float):
        raise ValueError(f"format_p_value should only be applied to P-value float. But got: {type(x)}.")
    if not isinstance(x, PValue):
        raise RunUtilsError(
            RunIssue(
                code_problem=CodeProblem.RuntimeError,
                issue=f"It seems like you are applying format_p_value to some values that are not P-values.",
                instructions=f"No need to apply format_p_value to these values.",
            )
        )
