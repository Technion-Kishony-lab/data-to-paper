import numbers
import re
from typing import Dict, Union

import numpy as np
import pandas as pd

from data_to_paper.run_gpt_code.overrides.pvalue import is_p_value, PValue
from data_to_paper.run_gpt_code.run_issues import CodeProblem, RunIssue, RunIssues
from data_to_paper.utils import dedent_triple_quote_str

MAX_COLUMNS = 10
MAX_ROWS = 20


def _is_non_integer_numeric(value) -> bool:
    """
    Check if the value is a non-integer numeric.
    """
    if not isinstance(value, float):
        return False
    if is_p_value(value):
        return False
    if value.is_integer():
        return False
    # check if the value is nan or inf
    if np.isinf(value) or np.isnan(value):
        return False
    return True


# WIP for future use
def get_table_width(df: pd.DataFrame) -> float:
    """
    Calculate the width of the table in characters.

    Go over each column, and take the max of the length of the column name and the max of the length of the values.
    Should account for multi-index columns.
    """

    value_widths = [max(len(str(val)) for val in df.iloc[:, col_num]) for col_num in range(df.shape[1])]
    column_header_widths = np.zeros(df.columns.nlevels, df.shape[1])
    for level in range(df.columns.nlevels):
        is_repeated = df.columns.get_level_values(level).duplicated()
        column_header_widths[level, is_repeated] = 0
        column_header_widths[level, ~is_repeated] = \
            [len(str(val)) for val in df.columns.get_level_values(level)[~is_repeated]]
    column_header_widths = column_header_widths.max(axis=0)
    return sum(max(value_width, column_header_width)
               for value_width, column_header_width in zip(value_widths, column_header_widths))


def check_df_has_only_numeric_str_bool_or_tuple_values(df: pd.DataFrame, filename: str) -> RunIssues:
    """
    Check if the dataframe has only numeric, str, bool, or tuple values.
    """
    issues = RunIssues()
    for value in df.values.flatten():
        if isinstance(value, (pd.Series, pd.DataFrame)):
            issues.append(RunIssue(
                category='Checking df: wrong values',
                item=filename,
                issue=f"Something wierd in your dataframe. Iterating over df.values.flatten() "
                      f"returned a `{type(value).__name__}` object.",
                code_problem=CodeProblem.OutputFileContentLevelA,
            ))
            return issues

    un_allowed_type_names = {f'`{type(value).__name__}`' for value in df.values.flatten()
                             if not isinstance(value, (numbers.Number, str, bool, tuple, PValue))}
    if un_allowed_type_names:
        issues.append(RunIssue(
            category='Checking df: wrong values',
            item=filename,
            issue=f"Your dataframe contains values of types {sorted(un_allowed_type_names)} which are not supported.",
            instructions=f"Please make sure the saved dataframes have only numeric, str, bool, or tuple values.",
            code_problem=CodeProblem.OutputFileContentLevelA,
        ))
    return issues


def check_df_headers_are_int_str_or_bool(headers: Union[pd.MultiIndex, pd.Index], filename: str) -> RunIssues:
    """
    Check if the headers of the dataframe are int, str, or bool.
    """
    issues = RunIssues()
    if isinstance(headers, pd.MultiIndex):
        headers = [label for level in range(headers.nlevels) for label in headers.get_level_values(level)]
    for header in headers:
        if not isinstance(header, (int, str, bool)):
            issues.append(RunIssue(
                category='Checking df: wrong header',
                item=filename,
                issue=f"Your dataframe has a column header `{header}` of type `{type(header).__name__}` "
                      f"which is not supported.",
                instructions=f"Please make sure the saved dataframes have only int, str, or bool headers.",
                code_problem=CodeProblem.OutputFileContentLevelA,
            ))
    return issues


def check_df_index_is_a_range(df: pd.DataFrame, filename: str) -> RunIssues:
    """
    Check if the index of the dataframe is just a numeric range.
    """
    issues = RunIssues()
    index_is_range = [ind for ind in df.index] == list(range(df.shape[0]))
    if index_is_range:
        issues.append(RunIssue(
            category='Checking df: index',
            code_problem=CodeProblem.OutputFileDesignLevelA,
            item=filename,
            issue=f'The index of the table {filename} is just a range from 0 to {df.shape[0] - 1}.',
            instructions=dedent_triple_quote_str("""
                Please revise the code making sure the table is built with an index that has meaningful row labels.

                Labeling row with sequential numbers is not common in scientific tables. 
                Though, if you are sure that starting each row with a sequential number is really what you want, \t
                then convert it from int to strings, so that it is clear that it is not a mistake.
                """),
        ))
    return issues


def check_df_filename(filename: str) -> RunIssues:
    """
    Check if the filename of the table is in the format `df_<number>.pkl`.
    """
    issues = RunIssues()
    if not re.match(pattern=r'^df_(\d+).pkl$', string=filename):
        issues.append(RunIssue.from_current_tb(
            category='Table filename',
            code_problem=CodeProblem.OutputFileContentLevelA,
            issue=f'The filename of the table should be in the format `df_<number>.pkl`, '
                  f'but got {filename}.',
        ))
    return issues


def check_df_for_repeated_values(df: pd.DataFrame, filename: str) -> RunIssues:
    """
    # Check if the table contains the same values in multiple cells
    """
    issues = RunIssues()
    df_values = [v for v in df.values.flatten() if _is_non_integer_numeric(v)]
    if len(df_values) != len(set(df_values)):
        # Find the positions of the duplicated values:
        duplicated_values = [v for v in df_values if df_values.count(v) > 1]
        example_value = duplicated_values[0]
        duplicated_value_positions = np.where(df.values == example_value)
        duplicated_value_positions = list(zip(*duplicated_value_positions))
        duplicated_value_positions = [f'({row}, {col})' for row, col in duplicated_value_positions]
        duplicated_value_positions = ', '.join(duplicated_value_positions)

        issues.append(RunIssue(
            category='Checking df: Overlapping values',
            code_problem=CodeProblem.OutputFileContentLevelC,
            item=filename,
            issue=f'Note that the Table {filename} includes the same values in multiple cells.\n'
                  f'For example, the value {example_value} appears in the following cells:\n'
                  f'{duplicated_value_positions}.',
            instructions=dedent_triple_quote_str("""
                This is likely a mistake and is surely confusing to the reader.
                Please revise the code so that the table does not repeat the same values in multiple cells.
                """),
        ))
    return issues


def check_df_for_repeated_values_in_prior_dfs(df: pd.DataFrame, filename: str,
                                              prior_tables: Dict[str, pd.DataFrame]) -> RunIssues:
    """
    Check if the table numeric values overlap with values in prior tables
    """
    issues = RunIssues()
    df_values = [v for v in df.values.flatten() if _is_non_integer_numeric(v)]
    for prior_name, prior_table in prior_tables.items():
        if prior_table is df:
            continue
        prior_table_values = [v for v in prior_table.values.flatten() if _is_non_integer_numeric(v)]
        if any(value in prior_table_values for value in df_values):
            issues.append(RunIssue(
                category='Checking df: Overlapping values',
                code_problem=CodeProblem.OutputFileContentLevelC,
                issue=f'Table "{filename}" includes values that overlap with values in table "{prior_name}".',
                instructions=dedent_triple_quote_str("""
                    In scientific tables, it is not customary to include the same values in multiple tables.
                    Please revise the code so that each table include its own unique data.
                    """),
            ))
    return issues


def check_df_is_describe(df: pd.DataFrame, filename: str) -> RunIssues:
    """
    Check if the table is a df.describe() table
    """
    issues = RunIssues()
    description_labels = ('mean', 'std', 'min', '25%', '50%', '75%', 'max')
    if set(description_labels).issubset(df.columns) or set(description_labels).issubset(df.index):
        issues.append(RunIssue(
            category='Checking df: min/max',
            code_problem=CodeProblem.OutputFileContentLevelA,
            item=filename,
            issue=f'The table includes mean, std, as well as quantiles and min/max values.',
            instructions=dedent_triple_quote_str("""
                Note that in scientific tables, it is not customary to include quantiles, or min/max values, \t
                especially if the mean and std are also included.
                Please revise the code so that the tables only include scientifically relevant statistics.
                """),
        ))
    return issues


def check_df_for_nan_values(df: pd.DataFrame, filename: str) -> RunIssues:
    """
    Check if the table has NaN values or PValue with value of nan
    """
    issues = RunIssues()
    df_with_raw_pvalues = df.applymap(lambda v: v.value if is_p_value(v) else v)
    isnull = pd.isnull(df_with_raw_pvalues)
    num_nulls = isnull.sum().sum()
    if num_nulls > 0:
        if num_nulls > 1:
            issue_text = f'Note that the table has {num_nulls} NaN values.'
        else:
            issue_text = f'Note that the table has a NaN value.'

        issue_text += f'\nHere is the `isnull` of the table:\n```\n{isnull.to_string()}\n```\n'

        issues.append(RunIssue(
            category='Checking df: NaN values',
            item=filename,
            code_problem=CodeProblem.OutputFileContentLevelC,
            issue=issue_text,
            instructions="Please revise the code to avoid NaN values in the created tables.\n"
                         "If the NaNs are legit and stand for missing values: replace them with the string '-'.\n"
                         "Otherwise, if they are computational errors, please revise the code to fix it.",
        ))
    return issues


def check_df_size(df: pd.DataFrame, filename: str) -> RunIssues:
    """
    Check if the table has too many columns or rows
    """
    issues = RunIssues()
    trimming_note = "Note that simply trimming the data is not always a good solution. " \
                    "You might instead want to think of a different representation/organization of the table."

    if df.shape[1] > MAX_COLUMNS:
        issues.append(RunIssue(
            category='Checking df: too many columns',
            code_problem=CodeProblem.OutputFileContentLevelB,
            item=filename,
            issue=f'The table has {len(df.columns)} columns, which is way too many for a scientific table.',
            instructions=f"Please revise the code so that created tables "
                         f"have just 2-5 columns and definitely not more than {MAX_COLUMNS}.\n" + trimming_note
        ))

    if df.shape[0] > MAX_ROWS:
        issues.append(RunIssue(
            category='Checking df: too many rows',
            code_problem=CodeProblem.OutputFileContentLevelB,
            item=filename,
            issue=f'The table has {df.shape[0]} rows, which is way too many for a scientific table.',
            instructions=f"Please revise the code so that created tables "
                         f"have a maximum of {MAX_ROWS} rows.\n" + trimming_note
        ))
    return issues


def check_output_df_for_content_issues(df: pd.DataFrame, filename: str,
                                       prior_dfs: Dict[str, pd.DataFrame] = None) -> RunIssues:
    prior_dfs = prior_dfs or {}
    issues = RunIssues()

    # Check if the table has only numeric, str, bool, or tuple values
    issues.extend(check_df_has_only_numeric_str_bool_or_tuple_values(df, filename))

    # Check if the headers of the dataframe are int, str, or bool
    issues.extend(check_df_headers_are_int_str_or_bool(df.columns, filename))
    issues.extend(check_df_headers_are_int_str_or_bool(df.index, filename))

    # Check if the index of the dataframe is just a numeric range
    issues.extend(check_df_index_is_a_range(df, filename))

    # Check if the table contains the same values in multiple cells
    # issues.extend(check_df_for_repeated_values(df, filename))
    # This test is disabled for now. There are too many false positives - true cases of repeated values,
    #  especially in df.describe() of small datasets.

    # Check if the table numeric values overlap with values in prior tables
    issues.extend(check_df_for_repeated_values_in_prior_dfs(df, filename, prior_dfs))
    if issues:
        return issues

    # Check if the df is a df.describe() table
    issues.extend(check_df_is_describe(df, filename))
    if issues:
        return issues

    # Check if the df has NaN values or PValue with value of nan
    issues.extend(check_df_for_nan_values(df, filename))

    # Check if the df has too many columns or rows
    issues.extend(check_df_size(df, filename))

    return issues
