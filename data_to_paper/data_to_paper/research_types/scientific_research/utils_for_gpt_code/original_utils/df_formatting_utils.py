import numbers
from typing import Dict, Any, Tuple, Optional

import numpy as np
import pandas as pd

P_VALUE_MIN = 1e-6


def format_p_value(x):
    """
    Format a p-value to a string.
    """
    if not isinstance(x, numbers.Number):
        return x
    if x > 1 or x < 0:
        raise ValueError(f"p-value should be in the range [0, 1]. Got: {x}")
    # check if nan or inf
    if np.isinf(x) or np.isnan(x):
        return str(x)
    return "{:.3g}".format(x) if x >= P_VALUE_MIN else "<{}".format(P_VALUE_MIN)


def is_str_in_df(df: pd.DataFrame, s: str):
    return any(s in level for level in getattr(df.index, 'levels', [df.index]) + \
               getattr(df.columns, 'levels', [df.columns]))


AbbrToNameDef = Dict[Any, Tuple[Optional[str], Optional[str]]]


def split_mapping(abbrs_to_names_and_definitions: AbbrToNameDef):
    abbrs_to_names = {abbr: name for abbr, (name, definition) in
                      abbrs_to_names_and_definitions.items() if name is not None}
    names_to_definitions = {name or abbr: definition for abbr, (name, definition) in
                            abbrs_to_names_and_definitions.items() if definition is not None}
    return abbrs_to_names, names_to_definitions

