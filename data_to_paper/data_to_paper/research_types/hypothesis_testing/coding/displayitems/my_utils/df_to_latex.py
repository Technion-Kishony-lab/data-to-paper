import pandas as pd

from data_to_paper.research_types.hypothesis_testing.coding.analysis.my_utils.df_to_latex import analysis_df_to_latex


def displayitems_df_to_latex(df: pd.DataFrame, filename: str, **kwargs):
    """
    Same as analysis_df_to_latex, but for displayitems.
    See docstring of analysis_df_to_latex for more information.
    """
    return analysis_df_to_latex(df, filename, **kwargs)
