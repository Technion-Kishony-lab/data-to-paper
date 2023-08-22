from typing import Set

import pandas as pd
from pandas import DataFrame


def _extract_from_multiindex(multi_idx) -> Set:
    return set(item for tuple_level in multi_idx for item in tuple_level)


def extract_df_column_labels(df: DataFrame) -> Set:
    if isinstance(df.columns, pd.MultiIndex):
        return _extract_from_multiindex(df.columns.values)
    return set(df.columns)


def extract_df_row_labels(df: DataFrame) -> Set:
    if isinstance(df.index, pd.MultiIndex):
        return _extract_from_multiindex(df.index.values)
    return set(df.index)


def extract_df_axes_labels(df: DataFrame, index: bool = True, header: bool = True, with_title: bool = True) -> Set:
    axes_labels = {}
    if header:
        axes_labels = extract_df_column_labels(df)
        if with_title:
            axes_labels |= {df.columns.name}
    if index:
        axes_labels |= extract_df_row_labels(df)
        if with_title:
            axes_labels |= {df.index.name}
    return axes_labels
