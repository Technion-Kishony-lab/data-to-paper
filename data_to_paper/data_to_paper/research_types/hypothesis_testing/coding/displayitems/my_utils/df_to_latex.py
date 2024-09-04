import pandas as pd

from data_to_paper.research_types.hypothesis_testing.check_df_to_funcs.df_checker import check_df_to_latex_displayitems
from data_to_paper.run_gpt_code.overrides.dataframes.df_with_attrs import save_as_list_info_df
from data_to_paper.run_gpt_code.run_contexts import IssueCollector
from data_to_paper.utils.check_type import raise_on_wrong_func_argument_types

from data_to_paper.llm_coding_utils.df_to_latex import df_to_latex


def _df_to_latex(df: pd.DataFrame, filename: str, **kwargs):
    """
    Replacement of df_to_latex to be used by LLM-writen code.
    Same as df_to_latex, but also checks for issues.
    """
    raise_on_wrong_func_argument_types(df_to_latex, df, filename, **kwargs)
    save_as_list_info_df('df_to_latex', df, filename, kwargs)
    IssueCollector.get_runtime_instance().issues.extend(check_df_to_latex_displayitems(df, filename, kwargs))
