import pandas as pd
from pandas import DataFrame

from data_to_paper.utils.types import ListBasedSet


def _extract_from_index_or_multiindex(index_or_multiindex, with_title: bool = True, string_only: bool = False
                                      ) -> ListBasedSet:
    if isinstance(index_or_multiindex, pd.MultiIndex):
        result = ListBasedSet(item for tuple_level in index_or_multiindex for item in tuple_level)
    else:
        result = ListBasedSet(index_or_multiindex)
    if with_title:
        result.add(index_or_multiindex.name)
    if string_only:
        result = ListBasedSet(item for item in result if isinstance(item, str))
    return result


def extract_df_column_labels(df: DataFrame, with_title: bool = True, string_only: bool = False) -> ListBasedSet:
    return _extract_from_index_or_multiindex(df.columns, with_title=with_title, string_only=string_only)


def extract_df_row_labels(df: DataFrame, with_title: bool = True, string_only: bool = False) -> ListBasedSet:
    return _extract_from_index_or_multiindex(df.index, with_title=with_title, string_only=string_only)


def extract_df_axes_labels(df: DataFrame, index: bool = True, header: bool = True, with_title: bool = True,
                           string_only: bool = False) -> ListBasedSet:
    axes_labels = ListBasedSet()
    if header:
        axes_labels |= extract_df_column_labels(df, with_title=with_title, string_only=string_only)
    if index:
        axes_labels |= extract_df_row_labels(df, with_title=with_title, string_only=string_only)
    return axes_labels
