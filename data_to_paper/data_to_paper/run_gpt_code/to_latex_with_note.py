import re
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from data_to_paper.latex.tables import create_threeparttable
from data_to_paper.utils import dedent_triple_quote_str
from .run_context import BaseRunContext, ProvideData, IssueCollector

from .types import CodeProblem, RunIssue


KNOWN_ABBREVIATIONS = ('std', 'BMI', 'P>|z|', 'P-value', 'Std.Err.', 'Std. Err.')


def is_name_an_unknown_abbreviation(name: str) -> bool:
    """
    Check if the name is abbreviated.
    """
    if not isinstance(name, str):
        return False
    if len(name) == 0:
        return False
    if name in KNOWN_ABBREVIATIONS:
        return False

    if not any(char.isalpha() for char in name):
        return False

    if len(name) == 1:
        return True

    if '.' in name or ':' in name:
        return True
    if name.islower() or name.istitle() or (name[0].isupper() and name[1:].islower()):
        return False
    return True


def _is_non_integer_numeric(value) -> bool:
    """
    Check if the value is a non-integer numeric.
    """
    if not isinstance(value, float):
        return False
    if value.is_integer():
        return False
    return True


def to_latex_with_note(df: pd.DataFrame, filename: str, *args,
                       note: str = None,
                       legend: Dict[str, str] = None,
                       columns: List[str] = None,
                       **kwargs):
    """
    Create a latex table with a note.
    Same as df.to_latex, but with a note and legend.
    Checks for argument values and issues.
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

    latex = _to_latex_with_note(df, filename, *args, note=note, legend=legend, **kwargs)

    issues = _check_for_issues(latex, df, filename, *args, note=note, legend=legend, **kwargs)
    IssueCollector.get_runtime_object().add_issues(issues)

    return latex


def _to_latex_with_note(df: pd.DataFrame, filename: Optional[str], *args,
                        note: str = None,
                        legend: Dict[str, str] = None,
                        **kwargs):
    """
    Create a latex table with a note.
    Same as df.to_latex, but with a note and legend.
    No check for argument values or issues.
    """
    assert 'columns' not in kwargs, "assumes columns is None"
    latex = df.to_latex(*args, **kwargs)
    latex = create_threeparttable(latex, note, legend)
    if filename is not None:
        with open(filename, 'w') as f:
            f.write(latex)
    return latex


def _to_latex_with_note_transpose(df: pd.DataFrame, filename: Optional[str], *args,
                                  note: str = None,
                                  legend: Dict[str, str] = None,
                                  **kwargs):
    assert 'columns' not in kwargs, "assumes columns is None"
    index = kwargs.pop('index', True)
    header = kwargs.pop('header', True)
    header, index = index, header
    return _to_latex_with_note(df.T, filename, *args, note=note, legend=legend, index=index, header=header, **kwargs)


def _check_for_issues(latex: str, df: pd.DataFrame, filename: str, *args,
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
    prior_tables: Dict[str, pd.DataFrame] = ProvideData.get_or_create_item('prior_tables', {})
    prior_tables[filename] = df

    """
    TABLE CONTENT
    """

    # Check table compilation
    compilation_func = ProvideData.get_item('compile_to_pdf_func')
    file_stem, _ = filename.split('.')
    with BaseRunContext.disable_all():
        e = compilation_func(latex, file_stem)

    # Check if the table numeric values overlap with values in prior tables
    for prior_name, prior_table in prior_tables.items():
        if prior_table is df:
            continue
        prior_table_values = [v for v in prior_table.values.flatten() if _is_non_integer_numeric(v)]
        df_values = [v for v in df.values.flatten() if _is_non_integer_numeric(v)]
        if any(value in prior_table_values for value in df_values):
            issues.append(RunIssue(
                category='Table contents should not overlap',
                code_problem=CodeProblem.OutputFileContentLevelC,
                issue=f'Table "{filename}" includes values that overlap with values in table "{prior_name}".',
                instructions=dedent_triple_quote_str("""
                    In scientific tables, it is not customary to include the same values in multiple tables.
                    Please revise the code so that each table include its own unique data.
                    """),
            ))
    if issues:
        return issues

    # Check if the table is a df.describe() table
    description_headers = ('mean', 'std', 'min', '25%', '50%', '75%', 'max')
    if set(description_headers).issubset(columns) or set(description_headers).issubset(df.index):
        issues.append(RunIssue(
            category='Quantiles and min/max values should not be included in scientific tables',
            code_problem=CodeProblem.OutputFileContentLevelA,
            item=filename,
            issue=f'The table includes mean, std, as well as quantiles and min/max values.',
            instructions=dedent_triple_quote_str("""
                Note that in scientific tables, it is not customary to include quantiles, or min/max values, \
                especially if the mean and std are also included.
                Please revise the code so that the tables only include scientifically relevant statistics.
                """),
        ))
    if issues:
        return issues

    # Check if the table has NaN or Inf values:
    if index:
        entire_df = df.reset_index(inplace=False)
    else:
        entire_df = df
    isnull = pd.isnull(entire_df).values
    isinf = np.isinf(df.apply(pd.to_numeric, errors='coerce')).values
    if np.any(isinf) or np.any(isnull):
        issues.append(RunIssue(
            category='NaN or Inf values were found in created tables',
            code_problem=CodeProblem.OutputFileContentLevelA,
            issue=f'Here is table {filename}:\n```latex\n{latex}\n```\n\nNote that the table has NaN/Inf values.',
            instructions=dedent_triple_quote_str("""
                Please revise the code so that the tables only include scientifically relevant statistics.
                """),
        ))

    # Check for repetitive values in a column
    for column_header in columns:
        data = df[column_header]
        if len(data.unique()) == 1 and len(data) > 5:
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
                    issue=f'The column "{column_header}" has the same unique value for all rows.',
                    instructions=dedent_triple_quote_str("""
                        Please revise the code so that it:
                        * Finds the unique values of the column
                        * Asserts that the len of unique values == 1
                        * Create the table without this column
                        * Add the unique value in the table note (use `note=` in the function `to_latex_with_note`). 
                        """),
                ))

    # Check if the table has too many columns
    MAX_COLUMNS = 10
    if len(columns) > MAX_COLUMNS:
        issues.append(RunIssue(
            category='Too many columns in a table',
            code_problem=CodeProblem.OutputFileContentLevelB,
            item=filename,
            issue=f'The table has {len(columns)} columns, which is way too many.',
            instructions=f"Please revise the code so that created tables have just 2-5 columns "
                         f"and definitely not more than {MAX_COLUMNS}.",
        ))

    # Check if the table has too many rows
    MAX_ROWS = 20
    if df.shape[0] > MAX_ROWS:
        issues.append(RunIssue(
            category='Too many rows in a table',
            code_problem=CodeProblem.OutputFileContentLevelB,
            item=filename,
            issue=f'The table has {df.shape[0]} rows, which is way too many.',
            instructions=f"Please revise the code so that created tables "
                         f"have a maximum of {MAX_ROWS} rows.",
        ))
    if issues:
        return issues

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
    elif e > 1.1:
        # Try to compile the transposed table:
        latex_transpose = _to_latex_with_note_transpose(df, None, *args, note=note, legend=legend, **kwargs)
        with BaseRunContext.disable_all():
            e_transpose = compilation_func(latex_transpose, file_stem + '_transpose')
        if isinstance(e_transpose, float) and e_transpose < 1.1:
            transpose_message = dedent_triple_quote_str("""\n
                - Alternatively, consider completely transposing the table. \
                Replace `to_latex_with_note(df, ...)` with `to_latex_with_note(df.T, ...)`
                """)
        else:
            transpose_message = ''

        if index:
            index_note = dedent_triple_quote_str("""\n
                - Rename the index to a shorter names. \
                Replace `to_latex_with_note(df, ...)` with `to_latex_with_note(df.reset_index(inplace=False), ...)` \
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

                - Drop unnecessary columns. \
                Use `to_latex_with_note(df, filename, columns=...)` to select only the columns you need.

                - Rename columns to shorter names. \
                Replace `to_latex_with_note(df, filename, ...)` with \
                `to_latex_with_note(df.rename(columns=...), filename, ...)`
                """) + index_note + transpose_message,
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

        if re.search(pattern=r'<.*\>', string=note):
            messages.append('The note of the table should not contain "<...>"')

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
                """),
        ))

    if issues:
        return issues

    # Check that any abbreviated row/column labels are explained in the legend
    if index:
        headers = [name for name in df.index]
    else:
        headers = []
    headers += [name for name in columns]
    abbr_names = [name for name in headers if is_name_an_unknown_abbreviation(name)]
    un_mentioned_abbr_names = [name for name in abbr_names if name not in legend]
    if un_mentioned_abbr_names:
        instructions = dedent_triple_quote_str("""
            Please revise the code making sure all abbreviated names are explained in their table legend.
            Add the missing abbreviations and their explanations as keys and values in the `legend` argument of the \
            function `to_latex_with_note`.
            """)
        if e < 0.9:
            instructions += dedent_triple_quote_str("""
                Alternatively, you can replace the abbreviated names with their full names in the table itself.
                """)
        if legend:
            issue = f'The legend of the table needs to include also the following abbreviated names:\n' \
                    f'{un_mentioned_abbr_names}'
        else:
            issue = f'The table needs a legend explaining the following abbreviated names:\n' \
                    f'{un_mentioned_abbr_names}'
        issues.append(RunIssue(
            category='Some abbreviated names are not explained in the table legend',
            code_problem=CodeProblem.OutputFileDesignLevelB,
            item=filename,
            issue=issue,
            instructions=instructions,
        ))

    # Check that the legend does not include any names that are not in the table
    if legend:
        un_mentioned_names = [name for name in legend if name not in headers]
        if un_mentioned_names:
            issues.append(RunIssue(
                category='The table legend include some keys that are not part of the table row or column headers.',
                code_problem=CodeProblem.OutputFileDesignLevelB,
                item=filename,
                issue=f'The legend of the table includes the following names that are not in the table:\n'
                      f'{un_mentioned_names}',
                instructions="Please revise the code making sure the legend keys and the table headers match.",
            ))

    return issues
