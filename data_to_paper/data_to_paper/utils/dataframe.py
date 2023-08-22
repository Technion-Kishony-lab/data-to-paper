from typing import Set

import pandas as pd
from pandas import DataFrame


def extract_from_multiindex(multi_idx) -> Set:
    return set(item for tuple_level in multi_idx for item in tuple_level)


def extract_df_column_headers(df: DataFrame) -> Set:
    if isinstance(df.columns, pd.MultiIndex):
        return extract_from_multiindex(df.columns.values)
    return set(df.columns)


def extract_df_row_headers(df: DataFrame) -> Set:
    if isinstance(df.index, pd.MultiIndex):
        return extract_from_multiindex(df.index.values)
    return set(df.index)


def extract_df_headers(df: DataFrame) -> Set:
    return extract_df_column_headers(df) | extract_df_row_headers(df)
