import pandas as pd

from data_to_paper.llm_coding_utils import df_to_figure
from data_to_paper.research_types.hypothesis_testing.check_df_to_funcs.df_checker import \
    raise_issue_if_filename_not_legit_df_tag
from data_to_paper.run_gpt_code.overrides.dataframes.df_with_attrs import save_as_func_call_df


def analysis_df_to_figure(df: pd.DataFrame, filename: str, **kwargs):
    """
    Replacement of df_to_figure to be used by LLM-writen code.
    We are not actually running df_to_figure (yet).
    Instead, we are just saving the function call.
    Tests and runs are done after the LLM-code is completed.
    """
    raise_issue_if_filename_not_legit_df_tag(filename)
    return save_as_func_call_df(df_to_figure, df, filename, kwargs)
