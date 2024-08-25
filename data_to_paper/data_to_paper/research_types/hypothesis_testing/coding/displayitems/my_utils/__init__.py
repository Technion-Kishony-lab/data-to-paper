"""
Contains functions that can be imported and used by LLM-writen code.
The functions in this package are overridden functions that search for issues before running the raw functions.
"""

from .df_to_latex import _df_to_latex as df_to_latex
from .df_to_figure import _df_to_figure as df_to_figure
from .df_formatting_utils import is_str_in_df, split_mapping, AbbrToNameDef
df_to_latex.__qualname__ = 'df_to_latex'
df_to_figure.__qualname__ = 'df_to_figure'
