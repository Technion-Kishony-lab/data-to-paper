import pandas as pd

from data_to_paper.llm_coding_utils import df_to_figure
from data_to_paper.research_types.hypothesis_testing.env import get_max_rows_and_columns
from data_to_paper.run_gpt_code.overrides.dataframes.df_with_attrs import save_as_list_info_df


def analysis_df_to_figure(df: pd.DataFrame, filename: str, raise_formatting_errors=False, **kwargs):
    """
    Replacement of df_to_figure to be used by LLM-writen code.
    """
    kind = kwargs.get('kind', 'bar')
    max_rows_and_columns_to_show = get_max_rows_and_columns(is_figure=True, kind=kind, to_show=True)
    df_to_figure(df, filename, raise_formatting_errors=raise_formatting_errors,
                 max_rows_and_columns_to_show=max_rows_and_columns_to_show, **kwargs)

    # save df to pickle with the func and kwargs
    save_as_list_info_df('df_to_figure', df, filename, kwargs)
