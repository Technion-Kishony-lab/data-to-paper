import pandas as pd

from ...analysis.my_utils.df_to_figure import analysis_df_to_figure


def displayitems_df_to_figure(df: pd.DataFrame, filename: str, label: str = None, **kwargs):
    """
    Replacement of df_to_figure to be used by LLM-writen code.
    Same as df_to_figure, but also checks for issues.
    """
    analysis_df_to_figure(df, filename, raise_formatting_errors=True, **kwargs)
