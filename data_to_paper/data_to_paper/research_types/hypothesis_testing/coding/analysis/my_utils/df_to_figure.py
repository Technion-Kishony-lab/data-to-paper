import pandas as pd

from data_to_paper.llm_coding_utils.df_to_figure import df_to_figure
from data_to_paper.research_types.hypothesis_testing.check_df_to_funcs.df_checker import check_df_to_figure_analysis
from data_to_paper.research_types.hypothesis_testing.env import get_max_rows_and_columns
from data_to_paper.run_gpt_code.overrides.dataframes.df_with_attrs import save_as_list_info_df

from data_to_paper.run_gpt_code.run_contexts import IssueCollector


def _df_to_figure(df: pd.DataFrame, filename: str, raise_formatting_errors=False, **kwargs):
    """
    Replacement of df_to_figure to be used by LLM-writen code.
    """

    call_df_to_figure_and_save_df(df, filename, raise_formatting_errors=raise_formatting_errors, **kwargs)
    IssueCollector.get_runtime_instance().issues.extend(check_df_to_figure_analysis(df, filename, kwargs))


def call_df_to_figure_and_save_df(df: pd.DataFrame, filename: str, raise_formatting_errors=False, **kwargs):
    kind = kwargs.get('kind', 'bar')
    max_rows_and_columns_to_show = get_max_rows_and_columns(is_figure=True, kind=kind, to_show=True)
    df_to_figure(df, filename, raise_formatting_errors=raise_formatting_errors,
                 max_rows_and_columns_to_show=max_rows_and_columns_to_show, **kwargs)

    # save df to pickle with the func and kwargs
    save_as_list_info_df('df_to_figure', df, filename, kwargs)
