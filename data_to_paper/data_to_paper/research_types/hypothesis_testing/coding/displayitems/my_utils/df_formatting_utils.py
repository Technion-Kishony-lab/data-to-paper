from typing import Dict, Any, Tuple, Optional

import pandas as pd


def is_str_in_df(df: pd.DataFrame, s: str):
    return any(s in level for level in getattr(df.index, 'levels', [df.index]) +
               getattr(df.columns, 'levels', [df.columns]))


AbbrToNameDef = Dict[Any, Tuple[Optional[str], Optional[str]]]


def split_mapping(abbrs_to_names_and_definitions: AbbrToNameDef):
    abbrs_to_names = {abbr: name for abbr, (name, definition) in
                      abbrs_to_names_and_definitions.items() if name is not None}
    names_to_definitions = {name or abbr: definition for abbr, (name, definition) in
                            abbrs_to_names_and_definitions.items() if definition is not None}
    return abbrs_to_names, names_to_definitions
