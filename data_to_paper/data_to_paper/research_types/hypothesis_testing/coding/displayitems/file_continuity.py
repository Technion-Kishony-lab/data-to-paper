from typing import List

import pandas as pd

from data_to_paper.run_gpt_code.overrides.dataframes.df_with_attrs import ListInfoDataFrame
from data_to_paper.run_gpt_code.run_issues import RunIssue, CodeProblem
from data_to_paper.utils import dedent_triple_quote_str


def _check_for_file_continuity(df: pd.DataFrame, filename: str) -> List[RunIssue]:
    if not isinstance(df, ListInfoDataFrame):
        return [
            RunIssue(
                category='File continuity',
                item=filename,
                issue=dedent_triple_quote_str(f"""
                    You can only use the loaded `df` object (you can change the loaded df, but replace it).
                    """),
                code_problem=CodeProblem.OutputFileContentLevelA,
            )
        ]
    previous_filename = df.extra_info[-1][2]
    should_be_filename = previous_filename + '_formatted'
    if filename != should_be_filename:
        return [
            RunIssue(
                category='File continuity',
                item=filename,
                issue=dedent_triple_quote_str(f"""
                    The file name of the loaded df was "{previous_filename}".
                    The current file name should be "{should_be_filename}" (instead of "{filename}").
                    """),
                code_problem=CodeProblem.OutputFileContentLevelA,
            )
        ]
    return []
