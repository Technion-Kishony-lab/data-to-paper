import pandas as pd

from data_to_paper.research_types.hypothesis_testing.check_df_to_funcs.df_checker import check_df_to_figure_displayitems
from data_to_paper.run_gpt_code.run_contexts import IssueCollector
from ...analysis.my_utils.df_to_figure import call_df_to_figure_and_save_df


def _df_to_figure(df: pd.DataFrame, filename: str, label: str = None, **kwargs):
    """
    Replacement of df_to_figure to be used by LLM-writen code.
    Same as df_to_figure, but also checks for issues.
    """
    call_df_to_figure_and_save_df(df, filename, raise_formatting_errors=True, **kwargs)
    IssueCollector.get_runtime_instance().issues.extend(check_df_to_figure_displayitems(df, filename, kwargs))
