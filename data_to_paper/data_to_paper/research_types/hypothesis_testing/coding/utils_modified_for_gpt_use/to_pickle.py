from typing import Dict

import pandas as pd
from pandas.core.frame import DataFrame

from data_to_paper.run_gpt_code.base_run_contexts import RegisteredRunContext
from data_to_paper.run_gpt_code.attr_replacers import AttrReplacer
from data_to_paper.run_gpt_code.overrides.pvalue import PValue
from data_to_paper.run_gpt_code.run_issues import CodeProblem, RunIssue

from .check_df_of_table import check_output_df_for_content_issues, check_df_filename


def _dataframe_to_pickle_with_checks(df: pd.DataFrame, path: str, *args,
                                     original_func=None, context_manager: AttrReplacer = None, **kwargs):
    """
    Save a data frame to a pickle file.
    Check for content issues.
    """
    if hasattr(context_manager, 'prior_tables'):
        prior_tables: Dict[str, pd.DataFrame] = context_manager.prior_tables
    else:
        prior_tables = {}
        context_manager.prior_tables = prior_tables
    prior_tables[path] = df

    if args or kwargs:
        raise RunIssue.from_current_tb(
            category='Use of `to_pickle`',
            issue="Please use `to_pickle(path)` with only the `path` argument.",
            instructions="Please do not specify any other arguments.",
            code_problem=CodeProblem.RuntimeError,
        )

    if not isinstance(path, str):
        raise RunIssue.from_current_tb(
            category='Use of `to_pickle`',
            issue="Please use `to_pickle(filename)` with a filename as a string argument in the format 'df_?'",
            code_problem=CodeProblem.RuntimeError,
        )
    context_manager.issues.extend(check_output_df_for_content_issues(df, path, prior_dfs=prior_tables))
    context_manager.issues.extend(check_df_filename(path))
    with RegisteredRunContext.temporarily_disable_all(), PValue.BEHAVE_NORMALLY.temporary_set(True):
        original_func(df, path)


def _read_pickle_and_save_filename(*args, original_func=None, context_manager: AttrReplacer = None, **kwargs):
    """
    Read a pickle file into a data frame.
    Save the filename.
    """
    filename = args[0] if args else kwargs.get('path', None)
    if filename:
        context_manager.last_read_pickle_filename = filename
    return original_func(*args, **kwargs)


def get_dataframe_to_pickle_attr_replacer():
    return AttrReplacer(obj_import_str='pandas.DataFrame', attr='to_pickle', wrapper=_dataframe_to_pickle_with_checks,
                        send_context_to_wrapper=True, send_original_to_wrapper=True)


def get_read_pickle_attr_replacer():
    context = AttrReplacer(obj_import_str='pandas', attr='read_pickle', wrapper=_read_pickle_and_save_filename,
                           send_context_to_wrapper=True, send_original_to_wrapper=True)
    context.last_read_pickle_filename = None
    return context


def _pickle_dump_with_checks(obj, file, *args, original_func=None, context_manager: AttrReplacer = None, **kwargs):
    """
    Save a Dict[str, Any] to a pickle file.
    Check for content issues.
    """
    filename = file.name
    category = 'Use of `pickle.dump`'
    if args or kwargs:
        raise RunIssue.from_current_tb(
            category=category,
            item=filename,
            issue="Please use `dump(obj, file)` with only the `obj` and `file` arguments.",
            instructions="Please do not specify any other arguments.",
            code_problem=CodeProblem.RuntimeError,
        )

    # Check if the object is a dictionary
    if isinstance(obj, DataFrame):
        raise RunIssue.from_current_tb(
            category=category,
            item=filename,
            issue="Please use `pickle.dump` only for saving the dictionary.",
            instructions="Use `df.to_pickle(filename)` for saving the table dataframes.",
            code_problem=CodeProblem.RuntimeError,
        )

    if not isinstance(obj, dict) or not all(isinstance(key, str) for key in obj.keys()):
        context_manager.issues.append(RunIssue.from_current_tb(
            category=category,
            item=filename,
            issue="Please use `dump(obj, filename)` with a dictionary `obj` with string keys.",
            code_problem=CodeProblem.RuntimeError,
        ))

    with PValue.BEHAVE_NORMALLY.temporary_set(True):
        original_func(obj, file)


def get_pickle_dump_attr_replacer():
    return AttrReplacer(obj_import_str='pickle', attr='dump', wrapper=_pickle_dump_with_checks,
                        send_context_to_wrapper=True, send_original_to_wrapper=True)
