import re
from typing import Dict, List

import numpy as np
import pandas as pd

from data_to_paper.run_gpt_code.overrides.types import PValue, is_p_value
from data_to_paper.run_gpt_code.types import CodeProblem, RunIssue
from data_to_paper.utils import dedent_triple_quote_str


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


def check_df_of_table_for_content_issues(df: pd.DataFrame, filename: str,
                                         prior_tables: Dict[str, pd.DataFrame]) -> List[RunIssue]:
    MAX_COLUMNS = 10
    MAX_ROWS = 20

    columns = df.columns

    issues = []

    # Check if index is just a range:
    index_is_range = [ind for ind in df.index] == list(range(df.shape[0]))
    if index_is_range:
        issues.append(RunIssue(
            category='Index is just a numeric range',
            code_problem=CodeProblem.OutputFileDesignLevelA,
            item=filename,
            issue=f'The index of the table {filename} is just a range from 0 to {df.shape[0] - 1}.',
            instructions=dedent_triple_quote_str("""
                Please revise the code making sure the table is built with an index that has meaningful row labels.

                Labeling row with sequential numbers is not common in scientific tables. 
                Though, if you are sure that starting each row with a sequential number is really what you want, \
                then convert it from int to strings, so that it is clear that it is not a mistake.
                """),
        ))

    # Check filename:
    if not re.match(pattern=r'^table_(\d+).pkl$', string=filename):
        issues.append(RunIssue(
            category='Table filename',
            code_problem=CodeProblem.OutputFileContentLevelA,
            issue=f'The filename of the table should be in the format `table_<number>.pkl`, '
                  f'but got {filename}.',
        ))

    # TODO: can delete, we are not using this anymore:
    with PValue.allow_str.temporary_set(True):
        printable_size_df = df.iloc[:MAX_ROWS, :MAX_COLUMNS]
        here_is_the_df = f'Here is the table {filename}:\n```\n{printable_size_df.to_string()}\n```\n'

    # Check if the table contains the same values in multiple cells
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
            category='Table contents should not overlap',
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

    # Check if the table numeric values overlap with values in prior tables
    for prior_name, prior_table in prior_tables.items():
        if prior_table is df:
            continue
        prior_table_values = [v for v in prior_table.values.flatten() if _is_non_integer_numeric(v)]
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
    description_labels = ('mean', 'std', 'min', '25%', '50%', '75%', 'max')
    if set(description_labels).issubset(columns) or set(description_labels).issubset(df.index):
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

    # Check if the table has NaN values:
    isnull = pd.isnull(df).values
    num_nulls = np.sum(isnull)
    if num_nulls > 0:
        # find the position of just the first nan:
        nan_positions = np.where(isnull)
        nan_positions = list(zip(*nan_positions))
        nan_positions = [f'({row}, {col})' for row, col in nan_positions]
        first_nan_position = nan_positions[0]
        if num_nulls > 1:
            issue_text = f'Note that the table has {num_nulls} NaN values.\n' \
                         f'For example, the first NaN value appears in the following cell:\n' \
                         f'{first_nan_position}.'
        else:
            issue_text = f'Note that the table has a NaN value in the following cell:\n' \
                         f'{first_nan_position}.'

        issues.append(RunIssue(
            category='NaN values were found in created tables',
            item=filename,
            code_problem=CodeProblem.OutputFileContentLevelC,
            issue=issue_text,
            instructions="Please revise the code to avoid NaN values in the created tables.\n"
                         "If the NaNs are legit and stand for missing values: replace them with the string '-'.\n"
                         "Otherwise, if they are computational errors, please revise the code to fix it.",
        ))

    # Check if the table has too many columns
    if len(columns) > MAX_COLUMNS:
        issues.append(RunIssue(
            category='Too many columns in a table',
            code_problem=CodeProblem.OutputFileContentLevelB,
            item=filename,
            issue=f'The table has {len(columns)} columns, which is way too many for a scientific table.',
            instructions=f"Please revise the code so that created tables have just 2-5 columns "
                         f"and definitely not more than {MAX_COLUMNS}.",
        ))

    # Check if the table has too many rows
    if df.shape[0] > MAX_ROWS:
        issues.append(RunIssue(
            category='Too many rows in a table',
            code_problem=CodeProblem.OutputFileContentLevelB,
            item=filename,
            issue=f'The table has {df.shape[0]} rows, which is way too many for a scientific table.',
            instructions=f"Please revise the code so that created tables "
                         f"have a maximum of {MAX_ROWS} rows.",
        ))

    return issues
