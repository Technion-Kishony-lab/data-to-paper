from typing import Dict, Any, Tuple, Optional

import pandas as pd

from data_to_paper.utils.check_type import raise_on_wrong_func_argument_types_decorator
from data_to_paper.utils.dataframe import extract_df_axes_labels


def is_str_in_df(df: pd.DataFrame, s: str):
    return s in extract_df_axes_labels(df)


AbbrToNameDef = Dict[Any, Tuple[Optional[str], Optional[str]]]


@raise_on_wrong_func_argument_types_decorator
def split_mapping(abbrs_to_names_and_definitions: AbbrToNameDef):
    abbrs_to_names = {abbr: name for abbr, (name, definition) in
                      abbrs_to_names_and_definitions.items() if name is not None}
    names_to_definitions = {name or abbr: definition for abbr, (name, definition) in
                            abbrs_to_names_and_definitions.items() if definition is not None}
    return abbrs_to_names, names_to_definitions
