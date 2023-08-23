import re
from typing import Dict, List, Optional

import pandas as pd

from data_to_paper.utils import dedent_triple_quote_str
from data_to_paper.run_gpt_code.overrides.types import PValue
from data_to_paper.env import TRACK_P_VALUES

from data_to_paper.run_gpt_code.base_run_contexts import RegisteredRunContext
from data_to_paper.run_gpt_code.run_contexts import ProvideData, IssueCollector

from data_to_paper.run_gpt_code.types import CodeProblem, RunIssue, RunUtilsError
from data_to_paper.utils.dataframe import extract_df_row_labels, extract_df_column_labels, \
    extract_df_axes_labels
from .format_p_value import is_ok_to_apply_format_p_value

from ..original_utils import to_latex_with_note

KNOWN_ABBREVIATIONS = ('std', 'BMI', 'P>|z|', 'P-value', 'Std.', 'Std', 'Err.', 'Avg.', 'Coef.', 'SD', 'SE', 'CI')

P_VALUE_STRINGS = ('P>|z|', 'P-value', 'P>|t|', 'P>|F|')


def _to_latex_with_note(df: pd.DataFrame, filename: str, caption: str = None, label: str = None,
                        note: str = None,
                        legend: Dict[str, str] = None,
                        columns: List[str] = None,
                        **kwargs):
    """
    Replacement of to_latex_with_note tp be used by ChatGPT code.
    Same as to_latex_with_note, but also checks for issues.
    """
    if not isinstance(df, pd.DataFrame):
        raise ValueError(f'Expected `df` to be a pandas.DataFrame, got {type(df)}')

    if not isinstance(filename, str):
        raise ValueError(f'Expected `filename` to be a string, got {type(filename)}')

    if not filename.endswith('.tex'):
        raise ValueError(f'Expected `filename` to end with .tex, got {filename}')

    if not isinstance(note, str) and note is not None:
        raise ValueError(f'Expected `note` to be a string or None, got {type(note)}')

    if isinstance(legend, dict):
        if not all(isinstance(key, str) for key in legend.keys()):
            raise ValueError(f'Expected `legend` keys to be strings, got {legend.keys()}')
        if not all(isinstance(value, str) for value in legend.values()):
            raise ValueError(f'Expected `legend` values to be strings, got {legend.values()}')
    elif legend is not None:
        raise ValueError(f'Expected legend to be a dict or None, got {type(legend)}')

    if columns is not None:
        df = df[columns]

    issues = _check_for_table_style_issues(df, filename, caption=caption, label=label, note=note, legend=legend,
                                           **kwargs)
    IssueCollector.get_runtime_instance().issues.extend(issues)

    with PValue.allow_str.temporary_set(True):
        return to_latex_with_note(df, filename, caption=caption, label=label, note=note, legend=legend, **kwargs)


def to_latex_with_note_transpose(df: pd.DataFrame, filename: Optional[str], *args,
                                 note: str = None,
                                 legend: Dict[str, str] = None,
                                 **kwargs):
    assert 'columns' not in kwargs, "assumes columns is None"
    index = kwargs.pop('index', True)
    header = kwargs.pop('header', True)
    header, index = index, header
    return to_latex_with_note(df.T, filename, *args, note=note, legend=legend, index=index, header=header, **kwargs)


def contains_both_letter_and_numbers(name: str) -> bool:
    """
    Check if the name contains both letters and numbers.
    """
    return any(char.isalpha() for char in name) and any(char.isdigit() for char in name)


def is_unknown_abbreviation(name: str) -> bool:
    """
    Check if the name is abbreviated.
    """
    if not isinstance(name, str):
        return False

    if len(name) == 0:
        return False

    if len(name) <= 2:
        return True

    if name.isnumeric():
        return False

    for abbreviation in KNOWN_ABBREVIATIONS:
        if abbreviation.endswith('.'):
            pattern = r'\b' + re.escape(abbreviation)
        else:
            pattern = r'\b' + re.escape(abbreviation) + r'\b'
        name = re.sub(pattern, '', name)

    # if there are no letters left, it is not an abbreviation
    if not any(char.isalpha() for char in name):
        return False

    words = re.split(pattern=r'[-_ =(),]', string=name)
    if any(contains_both_letter_and_numbers(word) for word in words):
        return True

    # if there are over 3 words, it is not an abbreviation:
    if len(re.split(pattern=r' ', string=name)) >= 3:
        return False

    if '.' in name or ':' in name or '_' in name:
        return True
    words = re.split(pattern=r'[-_ ]', string=name)
    words = [word for word in words if word != '']
    if all((word.islower() or word.istitle()) for word in words):
        return False
    return True


def _check_for_table_style_issues(df: pd.DataFrame, filename: str, *args,
                                  note: str = None,
                                  legend: Dict[str, str] = None,
                                  **kwargs) -> List[RunIssue]:
    assert 'columns' not in kwargs, "assumes columns is None"
    columns = df.columns
    caption = kwargs.get('caption', None)
    label = kwargs.get('label', None)
    index = kwargs.get('index', True)
    legend = {} if legend is None else legend

    issues = []

    # Check table compilation
    try:
        compilation_func = ProvideData.get_item('compile_to_pdf_func')
    except RuntimeError:
        compilation_func = None

    file_stem, _ = filename.split('.')
    with RegisteredRunContext.temporarily_disable_all(), \
            PValue.allow_str.temporary_set(True):
        latex = to_latex_with_note(df, None, *args, note=note, legend=legend, **kwargs)
        if compilation_func is None:
            e = 0
        else:
            e = compilation_func(latex, file_stem)

    index_is_range = [ind for ind in df.index] == list(range(df.shape[0]))

    # Enforce index=True:
    if not index:
        if index_is_range:
            msg = 'Your current df index is just a numeric range range, so you will have to re-specify the index. ' \
                  'If there is a column that should be the index, use `df.set_index(...)` to set it as the index.'
        else:
            msg = ''
        issues.append(RunIssue(
            code_problem=CodeProblem.OutputFileDesignLevelA,
            item=filename,
            issue=f'Do not call `to_latex_with_note` with `index=False`. '
                  f'I want to be able to extract the row labels from the index.',
            instructions=dedent_triple_quote_str("""
                Please revise the code making sure all tables are created with `index=True`, and that the index is \
                meaningful.
                """) + msg,
        ))
    if issues:
        return issues

    if issues:
        return issues

    # Get all labels:

    axes_labels = extract_df_axes_labels(df, index=index)
    axes_labels = {axes_label for axes_label in axes_labels if isinstance(axes_label, str)}

    """
    TABLE CONTENT
    """

    # Check for repetitive values in a column

    for icol in range(df.shape[1]):
        column_label = df.columns[icol]
        data = df.iloc[:, icol]
        try:
            data_unique = data.unique()
        except:
            data_unique = None
        if data_unique is not None and len(data_unique) == 1 and len(data) > 5:
            data0 = data.iloc[0]
            # check if the value is a number
            if not isinstance(data0, (int, float)):
                pass
            elif round(data0) == data0 and data0 < 10:
                pass
            else:
                issues.append(RunIssue(
                    category='Repetitive values in a column',
                    code_problem=CodeProblem.OutputFileContentLevelA,
                    item=filename,
                    issue=f'The column "{column_label}" has the same unique value for all rows.',
                    instructions=dedent_triple_quote_str(f"""
                        Please revise the code so that it:
                        * Finds the unique values \
                        (use `{column_label}_unique = df["{column_label}"].unique()`)
                        * Asserts that there is only one value. \
                        (use `assert len({column_label}_unique) == 1`)
                        * Creates the table without this column (use `df.drop(columns=["{column_label}"])`)
                        * Adds the unique value, {column_label}_unique[0], \
                        in the table note (use `note=` in the function `to_latex_with_note`).

                        There is no need to add corresponding comments to the code. 
                        """),
                ))

    # Check P-value formatting
    if TRACK_P_VALUES:
        # Check if the entire table is p-values:
        if sum(isinstance(v, PValue) for v in df.values.flatten()) > 1 \
                and all(is_ok_to_apply_format_p_value(v) for v in df.values.flatten()):
            raise RunUtilsError(
                RunIssue(
                    category='P-value formatting',
                    code_problem=CodeProblem.RuntimeError,
                    item=filename,
                    issue='P-values should be formatted with `format_p_value` before calling `to_latex_with_note`',
                    instructions=dedent_triple_quote_str(f"""
                        In particular, the dataframe should be formatted as:
                        `df = df.applymap(format_p_value)`
                        """),
                ))

        # Check if there are columns which are all p-values:
        p_value_columns = []
        for icol in range(df.shape[1]):
            column_label = df.columns[icol]
            data = df.iloc[:, icol]
            if any(isinstance(v, PValue) for v in data) \
                    and all(is_ok_to_apply_format_p_value(v) for v in data):
                p_value_columns.append(column_label)
        if p_value_columns:
            if len(p_value_columns) == 1:
                p_value_columns = p_value_columns[0]
            raise RunUtilsError(
                RunIssue(
                    category='P-value formatting',
                    code_problem=CodeProblem.RuntimeError,
                    item=filename,
                    issue='P-values should be formatted with `format_p_value`',
                    instructions=f'In particular, the p-value columns should be formatted as:\n'
                                 f'`df[{repr(p_value_columns)}] = df[{repr(p_value_columns)}].apply(format_p_value)`',
                ))
        # Check if there is a row which is all p-values:
        p_value_rows = []
        for irow in range(df.shape[0]):
            row_label = df.index[irow]
            data = df.iloc[irow, :]
            if any(isinstance(v, PValue) for v in data) \
                    and all(is_ok_to_apply_format_p_value(v) for v in data):
                p_value_rows.append(row_label)
        if p_value_rows:
            if len(p_value_rows) == 1:
                p_value_rows = p_value_rows[0]
            raise RunUtilsError(
                RunIssue(
                    category='P-value formatting',
                    code_problem=CodeProblem.RuntimeError,
                    item=filename,
                    issue='P-values should be formatted with `format_p_value`',
                    instructions=f'In particular, the p-value rows should be formatted as:\n'
                                 f'`df.loc[{repr(p_value_rows)}] = df.loc[{repr(p_value_rows)}].apply(format_p_value)`',
                ))

        # Check if there is a p-value that is not formatted:
        cells_with_p_value = []
        for irow in range(df.shape[0]):
            row_label = df.index[irow]
            for icol in range(df.shape[1]):
                column_label = df.columns[icol]
                v = df.iloc[irow, icol]
                if isinstance(v, PValue):
                    cells_with_p_value.append((row_label, column_label))
        if cells_with_p_value:
            row, col = cells_with_p_value[0]
            raise RunUtilsError(
                RunIssue(
                    category='P-value formatting',
                    code_problem=CodeProblem.RuntimeError,
                    item=filename,
                    issue='P-values should be formatted with `format_p_value`',
                    instructions=f"In particular, the dataframe has P-value in the cells: {cells_with_p_value}.\n"
                                 f"Please format them using `format_p_value` "
                                 f"(e.g., `df.loc[{repr(row)}, {repr(col)}] = "
                                 f"format_p_value(df.loc[{repr(row)}, {repr(col)}]).",
                ))

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
        latex_transpose = to_latex_with_note_transpose(df, None, *args, note=note, legend=legend, **kwargs)
        with RegisteredRunContext.temporarily_disable_all():
            e_transpose = compilation_func(latex_transpose, file_stem + '_transpose')
        if isinstance(e_transpose, float) and e_transpose < 1.1:
            transpose_message = dedent_triple_quote_str("""\n
                - Alternatively, consider completely transposing the table. Use `df = df.T`.
                """)
        else:
            transpose_message = ''
        if all(len(label) < 10 for label in axes_labels):
            drop_column_message = dedent_triple_quote_str("""\n
                - Drop unnecessary columns. \
                If the labels cannot be shortened much, consider whether there might be any \
                unnecessary columns that we can drop. \
                Use `to_latex_with_note(df, filename, columns=...)`.
                """)
        else:
            drop_column_message = ''
        if index:
            index_note = dedent_triple_quote_str("""\n
                - Rename the index labels to a shorter names. Use `df.rename(index=...)`
                """)
        else:
            index_note = ''

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
            instructions=dedent_triple_quote_str("""                
                Please change the code to make the table narrower. Consider any of the following options:

                - Rename column labels to shorter names. Use `df.rename(columns=...)`
                """) + index_note + drop_column_message + transpose_message,
            code_problem=CodeProblem.OutputFileContentLevelC,
        ))

    if issues:
        return issues

    """
    TABLE DESIGN
    """

    # Check that the rows are labeled:
    if index is False and df.shape[0] > 1 and df[columns[0]].dtype != 'object':
        issues.append(RunIssue(
            category='Unlabelled rows in a table',
            code_problem=CodeProblem.OutputFileDesignLevelA,
            item=filename,
            issue=f'The table has more than one row, but the rows are not labeled.',
            instructions=dedent_triple_quote_str("""
                Please revise the code making sure all tables are created with labeled rows.
                Use `index=True` in the function `to_latex_with_note`.
                """),
        ))
    if issues:
        return issues

    # Check caption/label
    messages = []
    if label is not None:
        if not label.startswith('table:'):
            messages.append('The label of the table is not in the format `table:<your table label here>`')
    else:
        messages.append(f'The table does not have a label.')

    # check if the caption starts with "Table <number>"
    if caption is not None:
        if caption.lower().startswith('table'):
            messages.append('The caption of the table should not start with "Table ..."')

        if '...' in caption:
            messages.append('The caption of the table should not contain "..."')

        if re.search(pattern=r'<.*\>', string=caption):
            messages.append('The caption of the table should not contain "<...>"')
    else:
        messages.append(f'The table does not have a caption.')

    if note is not None:
        if '...' in note:
            messages.append('The note of the table should not contain "..."')

    if note is not None and caption is not None:
        if note.lower() == caption.lower():
            messages.append('The note of the table should not be the same as the caption.\n'
                            'Notes are meant to provide additional information, not to repeat the caption.')

    for message in messages:
        issues.append(RunIssue(
            category='Problem with table caption/label',
            code_problem=CodeProblem.OutputFileDesignLevelA,
            item=filename,
            issue=message,
            instructions=dedent_triple_quote_str("""
                Please revise the code making sure all tables are created with a caption and a label.
                Use the arguments `caption` and `label` of the function `to_latex_with_note`.
                Captions should be suitable for a table in a scientific paper.
                Labels should be in the format `table:<your table label here>`.
                In addition, you can add:
                - an optional note for further explanations \
                (use the argument `note` of the function `to_latex_with_note`)
                - a legend mapping any abbreviated row/column labels to their definitions \
                (use the argument `legend` of the function `to_latex_with_note`) 
                """),
        ))

    if issues:
        return issues

    # Check for un-allowed characters in labels
    UNALLOWED_CHARS = ['_', '{', '}']
    for label in axes_labels:
        for char in UNALLOWED_CHARS:
            if char in label:
                issues.append(RunIssue(
                    category=f'Table row/column labels contain "{char}" - which is not suitable for a scientific table',
                    code_problem=CodeProblem.OutputFileDesignLevelB,
                    item=filename,
                    issue=f'The table label "{label}" contains the character "{char}", which is not '
                          f'recommended for a scientific table.',
                    instructions=f'Please revise the code so that the table axes labels do not contain '
                                 f'the "{char}" characters, possibly by replacing them with a space, or a dash. '
                                 f'I do not want using "{char}" even not if properly latex escaped.',
                ))
    if issues:
        return issues

    # Check that any abbreviated row/column labels are explained in the legend
    abbr_labels = [label for label in axes_labels if is_unknown_abbreviation(label)]
    un_mentioned_abbr_labels = [label for label in abbr_labels if label not in legend]
    if un_mentioned_abbr_labels:
        instructions = dedent_triple_quote_str("""
            Please revise the code making sure all abbreviated labels are explained in their table legend.
            Add the missing abbreviations and their explanations as keys and values in the `legend` argument of the \
            function `to_latex_with_note`.
            """)
        if e < 0.9:
            instructions += dedent_triple_quote_str("""
                Alternatively, you can replace the abbreviated labels with their full names in the table itself.
                """)
        if legend:
            issue = f'The legend of the table needs to include also the following abbreviated labels:\n' \
                    f'{un_mentioned_abbr_labels}'
        else:
            issue = f'The table needs a legend explaining the following abbreviated labels:\n' \
                    f'{un_mentioned_abbr_labels}'
        issues.append(RunIssue(
            category='Some abbreviated labels are not explained in the table legend',
            code_problem=CodeProblem.OutputFileDesignLevelB,
            item=filename,
            issue=issue,
            instructions=instructions,
        ))

    # Check that the legend does not include any labels that are not in the table
    if legend:
        un_mentioned_labels = [label for label in legend if label not in axes_labels]
        if un_mentioned_labels:
            issues.append(RunIssue(
                category='The table legend include some keys that are not part of the table row or column labels.',
                code_problem=CodeProblem.OutputFileDesignLevelB,
                item=filename,
                issue=f'The legend of the table includes the following labels that are not in the table:\n'
                      f'{un_mentioned_labels}',
                instructions=dedent_triple_quote_str("""
                    Here are the table row and column labels:
                    {labels}
                    
                    The legend keys should represent a subset of the the table labels, which need clarification:
                    - labels that are abbreviated
                    - labels that are not self-explanatory
                    - labels that represent a categorical/ordinal variable that requires explanation of the
                      categories/levels
                    
                    Please revise the code changing either the legend keys, or the table labels, accordingly.
                    
                    As a reminder: you can use the `note` argument to add information that is related to the
                    table as a whole, rather than to a specific label.
                    """).format(labels=axes_labels)
            ))

    return issues
