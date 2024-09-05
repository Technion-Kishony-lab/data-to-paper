import pandas as pd

from data_to_paper.research_types.hypothesis_testing.coding.analysis.my_utils.df_to_latex import analysis_df_to_latex
from data_to_paper.run_gpt_code.overrides.dataframes.df_with_attrs import save_as_list_info_df
from data_to_paper.utils.check_type import raise_on_wrong_func_argument_types

from data_to_paper.llm_coding_utils.df_to_latex import df_to_latex


def displayitems_df_to_latex(df: pd.DataFrame, filename: str, **kwargs):
    """
    Replacement of df_to_latex to be used by LLM-writen code.
    Same as df_to_latex, but also checks for issues.
    """
    analysis_df_to_latex(df, filename, **kwargs)
