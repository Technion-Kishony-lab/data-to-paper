import re
from typing import Dict, List, Optional

import pandas as pd

from data_to_paper.utils import dedent_triple_quote_str
from data_to_paper.run_gpt_code.overrides.types import PValue
from data_to_paper.env import TRACK_P_VALUES

from data_to_paper.run_gpt_code.base_run_contexts import RegisteredRunContext
from data_to_paper.run_gpt_code.run_contexts import ProvideData, IssueCollector

from data_to_paper.run_gpt_code.types import CodeProblem, RunIssue, RunUtilsError
from .check_df_of_table import check_df_of_table_for_content_issues

from ..original_utils import to_latex_with_note
from ..original_utils.format_p_value import P_VALUE_MIN

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

    latex = to_latex_with_note(df, filename, caption=caption, label=label, note=note, legend=legend, **kwargs)

    return latex


def to_latex_with_note_transpose(df: pd.DataFrame, filename: Optional[str], *args,
                                 note: str = None,
                                 legend: Dict[str, str] = None,
                                 **kwargs):
    assert 'columns' not in kwargs, "assumes columns is None"
    index = kwargs.pop('index', True)
    header = kwargs.pop('header', True)
    header, index = index, header
    return to_latex_with_note(df.T, filename, *args, note=note, legend=legend, index=index, header=header, **kwargs)


def is_unknown_abbreviation(name: str) -> bool:
    """
    Check if the name is abbreviated.
    """
    if not isinstance(name, str):
        return False

    if len(name) == 0:
        return False

    if len(name) == 1:
        return True

    for abbreviation in KNOWN_ABBREVIATIONS:
        if abbreviation.endswith('.'):
            pattern = r'\b' + re.escape(abbreviation)
        else:
            pattern = r'\b' + re.escape(abbreviation) + r'\b'
        name = re.sub(pattern, '', name)

    # if there are no letters left, it is not an abbreviation
    if not any(char.isalpha() for char in name):
        return False

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

    """
    TABLE CONTENT
    """

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
                    instructions=dedent_triple_quote_str(f"""
                        Please revise the code so that it:
                        * Finds the unique values \
                        (use `{column_header}_unique = df["{column_header}"].unique()`)
                        * Asserts that there is only one value. \
                        (use `assert len({column_header}_unique) == 1`)
                        * Creates the table without this column (use `df.drop(columns=["{column_header}"])`)
                        * Adds the unique value, {column_header}_unique[0], \
                        in the table note (use `note=` in the function `to_latex_with_note`).

                        There is no need to add corresponding comments to the code. 
                        """),
                ))

    # Check P-value formatting
    if TRACK_P_VALUES:
        # Check if there is a column which is all p-values:
        for column_header in columns:
            # if any(column_header.lower() == p.lower() for p in P_VALUE_STRINGS):  # Column header is a p-value column
            if all(isinstance(v, PValue) for v in df[column_header]):
                raise RunUtilsError(
                    RunIssue(
                        category='P-value formatting',
                        code_problem=CodeProblem.RuntimeError,
                        item=filename,
                        issue='P-values should be formatted with `format_p_value`',
                        instructions=dedent_triple_quote_str(f"""
                            In particular, the p-value column "{column_header}" should be formatted as:
                            `df["{column_header}"] = df["{column_header}"].apply(format_p_value)`
                            """),
                    ))
        # Check if there is a row which is all p-values:
        for row_header in df.index:
            if all(isinstance(v, PValue) for v in df.loc[row_header]):
                raise RunUtilsError(
                    RunIssue(
                        category='P-value formatting',
                        code_problem=CodeProblem.RuntimeError,
                        item=filename,
                        issue='P-values should be formatted with `format_p_value`',
                        instructions=dedent_triple_quote_str(f"""
                            In particular, the p-value row "{row_header}" should be formatted as:
                            `df.loc["{row_header}"] = df.loc["{row_header}"].apply(format_p_value)`
                            """),
                    ))

        # Check if there is a p-value that is not formatted:
        for column_header in columns:
            for row_header in df.index:
                v = df.loc[row_header, column_header]
                if isinstance(v, PValue):
                    raise RunUtilsError(
                        RunIssue(
                            category='P-value formatting',
                            code_problem=CodeProblem.RuntimeError,
                            item=filename,
                            issue='P-values should be formatted with `format_p_value`',
                            instructions=dedent_triple_quote_str(f"""
                                In particular, the dataframe should be formatted as:
                                `df.loc["{row_header}", "{column_header}"] = format_p_value({v})`
                                """),
                        ))


    latex = to_latex_with_note(df, filename, *args, note=note, legend=legend, **kwargs)

    # Check table compilation
    compilation_func = ProvideData.get_item('compile_to_pdf_func')
    file_stem, _ = filename.split('.')
    with RegisteredRunContext.temporarily_disable_all():
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
    elif e > 1.1:
        # Try to compile the transposed table:
        latex_transpose = to_latex_with_note_transpose(df, None, *args, note=note, legend=legend, **kwargs)
        with RegisteredRunContext.temporarily_disable_all():
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
                In addition, you can add:
                - an optional note for further explanations \
                (use the argument `note` of the function `to_latex_with_note`)
                - a legend mapping any abbreviated row/column labels to their definitions \
                (use the argument `legend` of the function `to_latex_with_note`) 
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
    abbr_names = [name for name in headers if is_unknown_abbreviation(name)]
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
                instructions=f"Here are the table headers:\n{headers}\n"
                             f"Please revise the code making sure the legend keys and the table headers match.",
            ))

    return issues
