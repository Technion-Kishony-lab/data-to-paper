# Utils made available to the LLM code for the data analysis step
from .df_to_figure import analysis_df_to_figure as df_to_figure
from .df_to_latex import analysis_df_to_latex as df_to_latex
df_to_latex.__qualname__ = 'df_to_latex'
df_to_figure.__qualname__ = 'df_to_figure'
