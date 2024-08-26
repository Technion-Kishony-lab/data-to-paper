import pandas as pd

from data_to_paper.llm_coding_utils.df_to_latex import df_to_latex
from data_to_paper.research_types.hypothesis_testing.coding.analysis.check_df_of_table import \
    check_output_df_for_content_issues
from data_to_paper.run_gpt_code.overrides.dataframes.df_with_attrs import save_as_list_info_df

from data_to_paper.run_gpt_code.run_contexts import IssueCollector


def _df_to_latex(df: pd.DataFrame, filename: str, **kwargs):
    """
    Replacement of df_to_latex to be used by LLM-writen code.
    Same as df_to_latex, but also checks for issues.
    """

    issue_collector = IssueCollector.get_runtime_instance()
    issues = check_output_df_for_content_issues(df, filename)
    issue_collector.issues.extend(issues)

    # call just to raise in wrong argument types:
    df_to_latex(df, filename, **kwargs, is_html=None)

    save_as_list_info_df('df_to_latex', df, filename, kwargs)
