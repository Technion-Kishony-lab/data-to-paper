import re
from typing import Dict, List, Optional

import pandas as pd

from data_to_paper.utils import dedent_triple_quote_str
from data_to_paper.run_gpt_code.overrides.pvalue import OnStr, is_containing_p_value

from data_to_paper.run_gpt_code.base_run_contexts import RegisteredRunContext
from data_to_paper.run_gpt_code.run_contexts import ProvideData, IssueCollector

from data_to_paper.run_gpt_code.run_issues import CodeProblem, RunIssue, RunIssues
from data_to_paper.utils.dataframe import extract_df_axes_labels
from .check_df_formatting import check_for_repetitive_value_in_column, checks_that_rows_are_labelled, \
    check_for_unallowed_characters, check_for_unexplained_abbreviations, \
    check_legend_does_not_include_labels_that_are_not_in_table, check_table_label, check_table_caption, \
    check_note_different_than_caption

from .check_df_of_table import check_df_headers_are_int_str_or_bool, check_df_of_table_for_content_issues
from .label_latex_source import wrap_source_filename_as_latex_comment

from ..original_utils import to_figure_with_note
from ..original_utils.to_latex_with_note import raise_on_wrong_params_for_to_latex_with_note


def _to_figure_with_note(df: pd.DataFrame, filename: str, caption: str = None, label: str = None,
                         legend: Dict[str, str] = None,
                         **kwargs):
    """
    Replacement of to_figure_with_note to be used by LLM-writen code.
    Same as to_figure_with_note, but also checks for issues.
    """
    raise_on_wrong_params_for_to_latex_with_note(df, filename, caption=caption, label=label, legend=legend)
    if not isinstance(filename, str):
        raise ValueError(f'Expected `filename` to be a string, got {type(filename)}')

    issues = _check_for_figure_style_issues(df, filename, caption=caption, label=label, note=note, legend=legend,
                                           **kwargs)
    IssueCollector.get_runtime_instance().issues.extend(issues)
    # get the ReadPickleAttrReplacer instance:
    pickle_filename = next((context.last_read_pickle_filename
                            for context in RegisteredRunContext.get_all_runtime_instances()
                            if context.name == 'ReadPickleAttrReplacer'), None)
    if pickle_filename:
        comment = wrap_source_filename_as_latex_comment(pickle_filename)
    else:
        comment = None

    latex = to_figure_with_note(df, filename, caption=caption, label=label, note=note, legend=legend,
                                pvalue_on_str=OnStr.LATEX_SMALLER_THAN,
                                comment=comment,
                                **kwargs)
    return latex


def _check_for_figure_style_issues(df: pd.DataFrame, filename: str, *args,
                                   note: str = None,
                                   legend: Dict[str, str] = None,
                                   **kwargs) -> RunIssues:
    caption: Optional[str] = kwargs.get('caption', None)
    label: Optional[str] = kwargs.get('label', None)
    legend = {} if legend is None else legend

    issues = check_df_of_table_for_content_issues(df, filename)
    if issues:
        return issues

    # Check for repetitive values in a column
    issues.extend(check_for_repetitive_value_in_column(df, filename))
    if issues:
        return issues

    # Check that the rows are labeled:
    issues.extend(checks_that_rows_are_labelled(df, filename, index))
    if issues:
        return issues

    # Check that the columns and rows are only strings, numbers, or booleans:
    issues.extend(check_df_headers_are_int_str_or_bool(df.columns, filename))
    issues.extend(check_df_headers_are_int_str_or_bool(df.index, filename))
    if issues:
        return issues

    # Check caption/label
    issues.extend(check_table_label(df, filename, label=label))
    issues.extend(check_table_caption(df, filename, text=caption, item_name='caption'))
    if note is not None:
        issues.extend(check_table_caption(df, filename, text=note, item_name='note'))
        issues.extend(check_note_different_than_caption(df, filename, note=note, caption=caption))
    if issues:
        return issues

    # Check for un-allowed characters in labels
    issues.extend(check_for_unallowed_characters(df, filename))
    if issues:
        return issues

    # Check that any abbreviated row/column labels are explained in the legend
    issues.extend(check_for_unexplained_abbreviations(df, filename, legend=legend, is_narrow=e < 0.8))

    # Check that the legend does not include any labels that are not in the table
    issues.extend(check_legend_does_not_include_labels_that_are_not_in_table(df, filename, legend=legend))
    return issues
