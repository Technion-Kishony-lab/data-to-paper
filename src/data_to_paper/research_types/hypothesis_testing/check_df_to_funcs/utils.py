from typing import Iterable, Union, Optional, Any, List

import numpy as np
import pandas as pd

from data_to_paper.run_gpt_code.overrides.pvalue import is_p_value


def is_non_integer_numeric(value) -> bool:
    """
    Check if the value is a non-integer numeric.
    """
    if not isinstance(value, float):
        return False
    if is_p_value(value):
        return False
    if value.is_integer():
        return False
    # check if the value is nan or inf
    if np.isinf(value) or np.isnan(value):
        return False
    return True


def _find_longest_str_in_list(lst: Iterable[Union[str, Any]]) -> Optional[str]:
    """
    Find the longest string in a list of strings.
    Only iterate over the str labels.
    """
    try:
        longest_str = None
        length = 0
        for label in lst:
            if isinstance(label, str) and len(label) > length:
                longest_str = label
                length = len(label)
        return longest_str
    except ValueError:
        return None


def _find_longest_labels_in_index(index: [pd.Index, pd.MultiIndex]) -> List[str]:
    """
    Find the longest label in the index.
    For multi-index, return the longest label in each level.
    Should only iterate over the str labels.
    """
    if isinstance(index, pd.MultiIndex):
        return [_find_longest_str_in_list(index.get_level_values(level).unique()) for level in range(index.nlevels)]
    else:
        return [_find_longest_str_in_list(index)]


def _find_longest_labels_in_columns_relative_to_content(df, tolerance: int = 2) -> List[str]:
    """
    For each column we need to check to what extent its label extends its content width (the width it would have if
    there was no label)
    """
    if isinstance(df.columns, pd.MultiIndex):
        # TODO: Implement for multi-index
        return []
    column_label_widths = np.array([len(label) for label in df.columns])
    column_content_widths = np.zeros_like(column_label_widths)
    for i, column in enumerate(df.columns):
        column_content_widths[i] = max(len(str(value)) for value in df[column])
    return df.columns[column_label_widths - column_content_widths > tolerance]
