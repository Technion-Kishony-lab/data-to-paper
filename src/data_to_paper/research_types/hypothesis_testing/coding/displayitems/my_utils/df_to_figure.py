import pandas as pd

from ...analysis.my_utils.df_to_figure import analysis_df_to_figure


def displayitems_df_to_figure(df: pd.DataFrame, filename: str, **kwargs):
    """
    Same as analysis_df_to_figure, but for displayitems.
    See docstring of analysis_df_to_figure for more information.
    """
    return analysis_df_to_figure(df, filename, **kwargs)
