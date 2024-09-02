from typing import Dict, List, Optional, Union, Iterable, Any

import numpy as np
import pandas as pd

from data_to_paper.utils import dedent_triple_quote_str
from data_to_paper.run_gpt_code.overrides.pvalue import OnStr, OnStrPValue

from data_to_paper.run_gpt_code.base_run_contexts import RegisteredRunContext
from data_to_paper.run_gpt_code.run_contexts import ProvideData, IssueCollector

from data_to_paper.run_gpt_code.run_issues import CodeProblem, RunIssue, RunIssues
from ..check_df_formatting import check_for_repetitive_value_in_column, checks_that_rows_are_labelled, \
    check_for_unallowed_characters, check_for_un_glossary_abbreviations, \
    check_glossary_does_not_include_labels_that_are_not_in_df, check_displayitem_caption, \
    check_note_different_than_caption
from ..file_continuity import _check_for_file_continuity

from ...analysis.check_df_of_table import check_df_headers_are_int_str_or_bool, check_output_df_for_content_issues
from ...analysis.my_utils import df_to_latex as analysis_df_to_latex

from data_to_paper.llm_coding_utils.df_to_latex import df_to_latex


def _find_longest_str_in_list(lst: Iterable[Union[str, Any]]) -> Optional[str]:
    """
    Find the longest string in a list of strings.
    Only iterate over the str labels.
    """
    try:
        longest_str = None
        length = 0
        for label in lst:
            if isinstance(label, str) and len(label) > length:
                longest_str = label
                length = len(label)
        return longest_str
    except ValueError:
        return None


def _find_longest_labels_in_index(index: [pd.Index, pd.MultiIndex]) -> List[str]:
    """
    Find the longest label in the index.
    For multi-index, return the longest label in each level.
    Should only iterate over the str labels.
    """
    if isinstance(index, pd.MultiIndex):
        return [_find_longest_str_in_list(index.get_level_values(level).unique()) for level in range(index.nlevels)]
    else:
        return [_find_longest_str_in_list(index)]


def _find_longest_labels_in_columns_relative_to_content(df, tolerance: int = 2) -> List[str]:
    """
    For each column we need to check to what extent its label extends its content width (the width it would have if
    there was no label)
    """
    if isinstance(df.columns, pd.MultiIndex):
        # TODO: Implement for multi-index
        return []
    column_label_widths = np.array([len(label) for label in df.columns])
    column_content_widths = np.zeros_like(column_label_widths)
    for i, column in enumerate(df.columns):
        column_content_widths[i] = max(len(str(value)) for value in df[column])
    return df.columns[column_label_widths - column_content_widths > tolerance]


def _df_to_latex(df: pd.DataFrame, filename: str, **kwargs):
    """
    Replacement of df_to_latex to be used by LLM-writen code.
    Same as df_to_latex, but also checks for issues.
    """
    analysis_df_to_latex(df, filename, **kwargs)
    issues = IssueCollector.get_runtime_instance().issues
    issues.extend(_check_for_file_continuity(df, filename))
    issues.extend(_check_for_table_style_issues(df, filename, **kwargs))


def df_to_latex_transpose(df: pd.DataFrame, filename: Optional[str], *args,
                          note: str = None,
                          glossary: Dict[str, str] = None,
                          **kwargs):
    assert 'columns' not in kwargs, "assumes columns is None"
    index = kwargs.pop('index', True)
    header = kwargs.pop('header', True)
    header, index = index, header
    return df_to_latex(df.T, filename, note=note, glossary=glossary, index=index, header=header, **kwargs)


def _check_for_table_style_issues(df: pd.DataFrame, filename: str, *args,
                                  note: str = None,
                                  glossary: Dict[str, str] = None,
                                  **kwargs) -> RunIssues:
    assert 'columns' not in kwargs, "assumes columns is None"
    caption: Optional[str] = kwargs.get('caption', None)
    index: bool = kwargs.get('index', True)
    glossary = {} if glossary is None else glossary

    issues = check_output_df_for_content_issues(df, filename)
    if issues:
        return issues

    # Enforce index=True:
    issues.extend(checks_that_rows_are_labelled(df, filename, index=index))
    if issues:
        return issues

    # Check for repetitive values in a column
    issues.extend(check_for_repetitive_value_in_column(df, filename))
    if issues:
        return issues

    # Check table compilation
    try:
        compilation_func = ProvideData.get_item('compile_to_pdf_func')
    except RuntimeError:
        compilation_func = None

    file_stem = filename
    with RegisteredRunContext.temporarily_disable_all():
        with OnStrPValue(OnStr.SMALLER_THAN):
            latex = df_to_latex(df, filename, note=note, glossary=glossary, **kwargs)
        if compilation_func is None:
            e = 0.
        else:
            e = compilation_func(latex, file_stem)

    if not isinstance(e, float):
        issues.append(RunIssue(
            category='Table pdflatex compilation failure',
            item=filename,
            issue=dedent_triple_quote_str("""
                Here is the created table:

                ```latex
                {table}
                ```

                When trying to compile it using pdflatex, I got the following error:

                {error}

                """).format(filename=filename, table=latex, error=e),
            comment='Table compilation failed',
            code_problem=CodeProblem.OutputFileDesignLevelB,
        ))
    elif e > 1.3:
        # Try to compile the transposed table:
        with OnStrPValue(OnStr.SMALLER_THAN):
            latex_transpose = df_to_latex_transpose(df, None, *args, note=note, glossary=glossary, **kwargs)
        with RegisteredRunContext.temporarily_disable_all():
            e_transpose = compilation_func(latex_transpose, file_stem + '_transpose')
        if isinstance(e_transpose, float) and e_transpose < 1.1:
            transpose_message = dedent_triple_quote_str("""\n
                - Alternatively, consider completely transposing the table. Use `df = df.T`.
                """)
        else:
            transpose_message = ''
        index_note = ''
        column_note = ''
        if index:
            longest_index_labels = _find_longest_labels_in_index(df.index)
            longest_index_labels = [label for label in longest_index_labels if label is not None and len(label) > 6]
            with OnStrPValue(OnStr.SMALLER_THAN):
                longest_column_labels = _find_longest_labels_in_columns_relative_to_content(df)
            longest_column_labels = [label for label in longest_column_labels if len(label) > 6]
            if longest_index_labels:
                index_note = dedent_triple_quote_str(f"""\n
                    - Rename any long index labels to shorter names \t
                    (for instance, some long label(s) in the index are: {longest_index_labels}). \t
                    Use `df.rename(index=...)`
                    """)

            if longest_column_labels:
                column_note = dedent_triple_quote_str(f"""\n
                    - Rename any long column labels to shorter names \t
                    (for instance, some long label(s) in the columns are: {longest_column_labels}). \t
                    Use `df.rename(columns=...)`
                    """)

        if not index_note and not column_note and not transpose_message:
            drop_column_message = dedent_triple_quote_str("""\n
                - Drop unnecessary columns. \t
                If the labels cannot be shortened much, consider whether there might be any \t
                unnecessary columns that we can drop. \t
                Use `df_to_latex(df, filename, columns=...)`.
                """)
        else:
            drop_column_message = ''

        issues.append(RunIssue(
            category='Table too wide',
            comment='Table too wide',
            item=filename,
            issue=dedent_triple_quote_str("""
                Here is the created table:

                ```latex
                {table}
                ```
                I tried to compile it, but the table is too wide. 
                """).format(filename=filename, table=latex),
            instructions="Please change the code to make the table narrower. "
                         "Consider any of the following options:\n"
                         + index_note + column_note + drop_column_message + transpose_message,
            code_problem=CodeProblem.OutputFileContentLevelC,
        ))

    if issues:
        return issues

    """
    TABLE DESIGN
    """

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
    # issues.extend(check_displayitem_label(df, filename, label=label))
    issues.extend(check_displayitem_caption(df, filename, text=caption, item_name='caption'))
    if note is not None:
        issues.extend(check_displayitem_caption(df, filename, text=note, item_name='note'))
        issues.extend(check_note_different_than_caption(df, filename, note=note, caption=caption))
    if issues:
        return issues

    # Check for un-allowed characters in labels
    issues.extend(check_for_unallowed_characters(df, filename))
    if issues:
        return issues

    # Check that any abbreviated row/column labels are explained in the glossary
    issues.extend(check_for_un_glossary_abbreviations(df, filename, glossary=glossary, is_narrow=e < 0.8))

    # Check that the glossary does not include any labels that are not in the table
    issues.extend(check_glossary_does_not_include_labels_that_are_not_in_df(df, filename, glossary=glossary))
    return issues
