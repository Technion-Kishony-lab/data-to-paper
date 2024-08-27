import pandas as pd
from pandas import DataFrame

from data_to_paper.utils.types import ListBasedSet


def _extract_from_multiindex(multi_idx) -> ListBasedSet:
    return ListBasedSet(item for tuple_level in multi_idx for item in tuple_level)


def extract_df_column_labels(df: DataFrame, with_title: bool = True) -> ListBasedSet:
    if isinstance(df.columns, pd.MultiIndex):
        result = _extract_from_multiindex(df.columns.values)
    else:
        result = ListBasedSet(df.columns)
    if with_title:
        result |= {df.columns.name}
    return result


def extract_df_row_labels(df: DataFrame, with_title: bool = True) -> ListBasedSet:
    if isinstance(df.index, pd.MultiIndex):
        result = _extract_from_multiindex(df.index.values)
    else:
        result = ListBasedSet(df.index)
    if with_title:
        result |= {df.index.name}
    return result


def extract_df_axes_labels(df: DataFrame, index: bool = True, header: bool = True, with_title: bool = True
                           ) -> ListBasedSet:
    axes_labels = ListBasedSet()
    if header:
        axes_labels |= extract_df_column_labels(df, with_title=with_title)
    if index:
        axes_labels |= extract_df_row_labels(df, with_title=with_title)
    return axes_labels
