from typing import Dict, Optional

import pandas as pd

from data_to_paper.run_gpt_code.run_contexts import IssueCollector
from data_to_paper.run_gpt_code.run_issues import RunIssues

from ...analysis.check_df_of_table import check_df_headers_are_int_str_or_bool, check_output_df_for_content_issues
from ...analysis.my_utils import df_to_figure as analysis_df_to_figure
from ..check_df_formatting import check_for_repetitive_value_in_column, checks_that_rows_are_labelled, \
    check_for_unallowed_characters, check_for_un_glossary_abbreviations, \
    check_glossary_does_not_include_labels_that_are_not_in_df, check_displayitem_caption, \
    check_note_different_than_caption
from ...utils import convert_filename_to_label


def _df_to_figure(df: pd.DataFrame, filename: str, label: str = None, **kwargs):
    """
    Replacement of df_to_figure to be used by LLM-writen code.
    Same as df_to_figure, but also checks for issues.
    """
    analysis_df_to_figure(df, filename, **kwargs)
    label = convert_filename_to_label(filename, label)
    issues = _check_for_figure_style_issues(df, filename, label=label, **kwargs)
    IssueCollector.get_runtime_instance().issues.extend(issues)


def _check_for_figure_style_issues(df: pd.DataFrame, filename: str, *args,
                                   note: str = None,
                                   glossary: Dict[str, str] = None,
                                   **kwargs) -> RunIssues:
    caption: Optional[str] = kwargs.get('caption', None)
    label: Optional[str] = kwargs.get('label', None)
    glossary = {} if glossary is None else glossary
    index: bool = kwargs.get('use_index', True)

    issues = RunIssues()

    # Check for repetitive values in a column
    issues.extend(check_for_repetitive_value_in_column(df, filename, displayitem='figure'))
    if issues:
        return issues

    # Check that the rows are labeled:
    issues.extend(checks_that_rows_are_labelled(df, filename, index=index, displayitem='figure'))
    if issues:
        return issues

    # Check that the columns and rows are only strings, numbers, or booleans:
    issues.extend(check_df_headers_are_int_str_or_bool(df.columns, filename))
    issues.extend(check_df_headers_are_int_str_or_bool(df.index, filename))
    if issues:
        return issues

    # Check caption/label
    # issues.extend(check_displayitem_label(df, filename, label=label, displayitem='figure'))
    issues.extend(check_displayitem_caption(df, filename, text=caption, item_name='caption', displayitem='figure'))
    if note is not None:
        issues.extend(check_displayitem_caption(df, filename, text=note, item_name='note', displayitem='figure'))
        issues.extend(check_note_different_than_caption(df, filename, note=note, caption=caption, displayitem='figure'))
    if issues:
        return issues

    # Check for un-allowed characters in labels
    issues.extend(check_for_unallowed_characters(df, filename))
    if issues:
        return issues

    # Check that any abbreviated row/column labels are explained in the glossary
    issues.extend(
        check_for_un_glossary_abbreviations(df, filename, glossary=glossary, is_narrow=True, displayitem='figure'))

    # Check that the glossary does not include any labels that are not in the table
    issues.extend(
        check_glossary_does_not_include_labels_that_are_not_in_df(df, filename, glossary=glossary,
                                                                  displayitem='figure'))
    return issues
