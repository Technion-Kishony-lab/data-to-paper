from dataclasses import dataclass
from typing import Dict, List

import pandas as pd

from data_to_paper.latex.tables import create_threeparttable
from data_to_paper.utils import dedent_triple_quote_str
from .dynamic_code import get_prevent_file_open_context
from .run_context import get_runtime_object

from .runtime_issues_collector import get_runtime_issue_collector
from .types import CodeProblem, RunIssue


@dataclass
class RunUtilsError(Exception):
    issue: RunIssue


KNOWN_ABBREVIATIONS = ('std', 'BMI', 'P>|z|', 'P-value', 'Std.Err.', 'Std. Err.')


def is_name_an_unknown_abbreviated(name: str) -> bool:
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


def to_latex_with_note(df: pd.DataFrame, filename: str, *args,
                       note: str = None,
                       legend: Dict[str, str] = None,
                       **kwargs):
    if not isinstance(df, pd.DataFrame):
        raise ValueError(f'Expected df to be a pandas.DataFrame, got {type(df)}')

    if not isinstance(filename, str):
        raise ValueError(f'Expected filename to be a string, got {type(filename)}')

    if not filename.endswith('.tex'):
        filename = filename + '.tex'

    latex = df.to_latex(*args, **kwargs)

    latex = create_threeparttable(latex, note, legend)

    issues = _check_for_issues(latex, df, filename, *args, note=note, legend=legend, **kwargs)
    get_runtime_issue_collector().add_issues(issues)

    with open(filename, 'w') as f:
        f.write(latex)


def _to_latex_with_note_traspose(df: pd.DataFrame, filename: str, *args,
                                 note: str = None,
                                 legend: Dict[str, str] = None,
                                 **kwargs):
    columns = kwargs.pop('columns', None)
    columns = df.columns if columns is None else columns
    index = kwargs.pop('index', True)
    df = df.copy()
    if index:
        df = df.reset_index()
        index = False
    df = df[columns]
    df_transpose = df.T
    latex = df_transpose.to_latex(*args, **kwargs)
    latex = create_threeparttable(latex, note, legend)
    return latex


def _check_for_issues(latex: str, df: pd.DataFrame, filename: str, *args,
                      note: str = None,
                      legend: Dict[str, str] = None,
                      **kwargs) -> List[RunIssue]:
    caption = kwargs.get('caption', None)
    label = kwargs.get('label', None)
    index = kwargs.get('index', True)
    columns = kwargs.get('columns', None)
    columns = df.columns if columns is None else columns
    legend = {} if legend is None else legend

    issues = []

    """
    TABLE CONTENT
    """

    # Check table compilation
    compilation_func = get_runtime_object('compile_to_pdf_func')
    file_stem, _ = filename.split('.')
    with get_prevent_file_open_context().disable_prevention.temporary_set(True):
        e = compilation_func(latex, file_stem)

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
                         f"with a maximin of {MAX_ROWS} rows.",
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
        latex_transpose = _to_latex_with_note_traspose(df, None, *args, note=note, legend=legend, **kwargs)
        with get_prevent_file_open_context().disable_prevention.temporary_set(True):
            e_transpose = compilation_func(latex_transpose, file_stem + '_transpose')
        if isinstance(e_transpose, float) and e_transpose < 1.1:
            transpose_message = dedent_triple_quote_str("""
                - Alternatively, consider completely transposing the table. \
                Replace `to_latex_with_note(df, ...)` with `to_latex_with_note(df.T, ...)`
                """)
        else:
            transpose_message = ''

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

                - If the table has the dataframe index, you can rename the index to a shorter names.
                Replace `to_latex_with_note(df, ...)` with `to_latex_with_note(df.rename(index=...), ...)`
                """) + transpose_message,
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
    category = 'Problem with table caption/label'
    instructions = dedent_triple_quote_str("""
        Please revise the code making sure all tables are created with a caption and a label.
        Use the arguments `caption` and `label` of the function `to_latex_with_note`.
        Captions should be suitable for a table in a scientific paper.
        Labels should be in the format `table:<your table label here>`.
        """)
    code_problem = CodeProblem.OutputFileDesignLevelA
    if caption is None or label is None:
        missing = 'caption and label' if caption is None and label is None \
            else 'caption' if caption is None else 'label'
        issues.append(RunIssue(
            category=category,
            code_problem=code_problem,
            item=filename,
            issue=f'The table does not have a {missing}.',
            instructions=instructions,
        ))

    if label is not None and not label.startswith('table:'):
        issues.append(RunIssue(
            category=category,
            code_problem=code_problem,
            item=filename,
            issue='The label of the table is not in the format `table:<your table label here>`',
            instructions=instructions,
        ))

    # check if the caption starts with "Table <number>"
    if caption is not None and caption.lower().startswith('table'):
        issues.append(RunIssue(
            category=category,
            code_problem=code_problem,
            item=filename,
            issue='The caption of the table should not start with "Table ..."',
            instructions=instructions,
        ))

    if issues:
        return issues

    # Check that any abbreviated row/column labels are explained in the legend
    if index:
        headers = [name for name in df.index]
    else:
        headers = []
    headers += [name for name in columns]
    abbr_names = [name for name in headers if is_name_an_unknown_abbreviated(name)]
    un_mentioned_abbr_names = [name for name in abbr_names if name not in legend]
    if un_mentioned_abbr_names:
        instructions = dedent_triple_quote_str("""
            Please revise the code making sure all abbreviated names are explained in their table legend.
            Add the missing abbreviations and their explanations as keys and values in the `legend` argument of the \
            function `to_latex_with_note`.
            """)
        if e < 0.9:
            instructions += dedent_triple_quote_str("""
                Alternatively, you cna replace the abbreviated names with their full names in the table itself.
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
                instructions="Please revise the code making sure the legend includes only names that are in the table."
            ))

    return issues
