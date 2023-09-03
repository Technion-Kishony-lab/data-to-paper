from typing import Set

import pandas as pd
from pandas import DataFrame


def _extract_from_multiindex(multi_idx) -> Set:
    return set(item for tuple_level in multi_idx for item in tuple_level)


def extract_df_column_labels(df: DataFrame, with_title: bool = True) -> Set:
    if isinstance(df.columns, pd.MultiIndex):
        result = _extract_from_multiindex(df.columns.values)
    else:
        result = set(df.columns)
    if with_title:
        result |= {df.columns.name}
    return result


def extract_df_row_labels(df: DataFrame, with_title: bool = True) -> Set:
    if isinstance(df.index, pd.MultiIndex):
        result = _extract_from_multiindex(df.index.values)
    else:
        result = set(df.index)
    if with_title:
        result |= {df.index.name}
    return result


def extract_df_axes_labels(df: DataFrame, index: bool = True, header: bool = True, with_title: bool = True) -> Set:
    axes_labels = set()
    if header:
        axes_labels |= extract_df_column_labels(df, with_title=with_title)
    if index:
        axes_labels |= extract_df_row_labels(df, with_title=with_title)
    return axes_labels
