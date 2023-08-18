from typing import Dict

import pandas as pd
from pandas.core.frame import DataFrame

from data_to_paper.run_gpt_code.overrides.attr_replacers import AttrReplacer
from data_to_paper.run_gpt_code.overrides.types import PValue
from data_to_paper.run_gpt_code.types import RunIssue, CodeProblem, RunUtilsError
from .to_latex_with_note import check_for_df_content_issues


def to_pickle_with_checks(df: pd.DataFrame, path: str, *args,
                          original_func=None, context_manager: AttrReplacer = None, **kwargs):
    """
    Save a data frame to a csv file.
    Check for content issues.
    """
    if hasattr(context_manager, 'prior_tables'):
        prior_tables: Dict[str, pd.DataFrame] = context_manager.prior_tables
    else:
        prior_tables = {}
        context_manager.prior_tables = prior_tables
    prior_tables[path] = df

    if args or kwargs:
        raise RunUtilsError(issue=RunIssue(
            issue="Please use `to_pickle(path)` with only the `path` argument.",
            instructions="Please do not specify any other arguments.",
            code_problem=CodeProblem.RuntimeError,
        ))

    if not isinstance(path, str):
        raise RunUtilsError(issue=RunIssue(
            issue="Please use `to_pickle(filename)` with a filename as a string argument in the format 'table_x'",
            code_problem=CodeProblem.RuntimeError,
        ))
    with PValue.allow_str.temporary_set(True):
        csv = df.to_csv()
    context_manager.issues.append(check_for_df_content_issues(df, path, csv, prior_tables=prior_tables))
    original_func(df, path)


def get_to_pickle_attr_replacer():
    return AttrReplacer(cls=DataFrame, attr='to_pickle', wrapper=to_pickle_with_checks,
                        send_context_to_wrapper=True, send_original_to_wrapper=True)
