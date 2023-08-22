import re
from typing import Dict, List

import numpy as np
import pandas as pd

from data_to_paper.run_gpt_code.overrides.types import PValue
from data_to_paper.run_gpt_code.types import CodeProblem, RunIssue
from data_to_paper.utils import dedent_triple_quote_str


def _is_non_integer_numeric(value) -> bool:
    """
    Check if the value is a non-integer numeric.
    """
    if not isinstance(value, float):
        return False
    if value.is_integer():
        return False
    # check if the value is nan or inf
    if np.isfinite(value) or np.isnan(value):
        return False
    return True


def check_df_of_table_for_content_issues(df: pd.DataFrame, filename: str,
                                         prior_tables: Dict[str, pd.DataFrame]) -> List[RunIssue]:
    columns = df.columns

    issues = []

    # Check filename:
    if not re.match(pattern=r'^table_(\d+).pkl$', string=filename):
        issues.append(RunIssue(
            category='Table filename',
            code_problem=CodeProblem.OutputFileContentLevelA,
            issue=f'The filename of the table should be in the format `table_<number>.pkl`, '
                  f'but got {filename}.',
        ))

    with PValue.allow_str.temporary_set(True):
        here_is_the_df = f'Here is the table {filename}:\n```\n{df.to_string()}\n```\n'

    # Check if the table contains the same values in multiple cells
    df_values = [v for v in df.values.flatten() if _is_non_integer_numeric(v)]
    if len(df_values) != len(set(df_values)):
        issues.append(RunIssue(
            category='Table contents should not overlap',
            code_problem=CodeProblem.OutputFileContentLevelC,
            item=filename,
            issue=here_is_the_df + 'Note that the Table includes the same values in multiple cells.',
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
    entire_df = df.reset_index(inplace=False)
    isnull = pd.isnull(entire_df).values
    if np.any(isnull):
        issues.append(RunIssue(
            category='NaN values were found in created tables',
            code_problem=CodeProblem.OutputFileContentLevelA,
            issue=here_is_the_df + 'Note that the table has NaN values.',
            instructions="Please revise the code to avoid NaN values in the created tables.\n"
                         "If the NaNs are legit and stand for missing values: replace them with the string '-'.\n"
                         "Otherwise, if they are computational errors, please revise the code to fix it.",
        ))

    # Check if the table has too many columns
    MAX_COLUMNS = 10
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
    MAX_ROWS = 20
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
