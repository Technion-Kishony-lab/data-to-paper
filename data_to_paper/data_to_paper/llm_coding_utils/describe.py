from typing import Any, Optional

import numpy as np
from pandas import DataFrame, Series

from data_to_paper.code_and_output_files.referencable_text import label_numeric_value
from data_to_paper.run_gpt_code.overrides.dataframes.df_methods import STR_FLOAT_FORMAT
from data_to_paper.run_gpt_code.overrides.dataframes.utils import llm_readable_to_csv, to_latex_with_value_format
from data_to_paper.run_gpt_code.overrides.pvalue import is_p_value, PValue


def _label_p_value(p_value):
    if is_p_value(p_value):
        s = str(p_value)
        st_sign = PValue.ON_STR.st_sign()
        if st_sign and s.startswith(st_sign):
            return st_sign + label_numeric_value(s[len(st_sign):])
        return label_numeric_value(s)
    return p_value


def _get_formatters(should_format: bool):
    if not should_format:
        return {}
    return dict(
        numeric_formater=lambda x: label_numeric_value(STR_FLOAT_FORMAT(x)),
        object_formatter=_label_p_value
    )


def describe_value(value: Any) -> str:
    """
    Describe the value in a way that can be used as a short string.
    """
    if value is None:
        return 'None'
    if isinstance(value, str):
        return f"'{value}'"
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        return f'[{", ".join(describe_value(v) for v in value)}]'
    if isinstance(value, dict):
        return f'{{{", ".join(f"{describe_value(k)}: {describe_value(v)}" for k, v in value.items())}}}'
    if isinstance(value, tuple):
        return f'({", ".join(describe_value(v) for v in value)})'
    if isinstance(value, DataFrame):
        return f'DataFrame(shape={value.shape}, columns={value.columns})'
    if isinstance(value, Series):
        return f'Series(shape={value.shape}, type={value.dtype})'
    if isinstance(value, np.ndarray):
        return f'np.ndarray(shape={value.shape}, dtype={value.dtype})'
    return str(value)


def describe_df(df: DataFrame, max_rows: Optional[int] = 25, max_columns: Optional[int] = 10,
                should_format: bool = True) -> str:
    """
    Describe the DataFrame in a way that can be used as a short string.
    """
    num_lines = len(df)
    num_columns = len(df.columns)
    if max_columns is not None and num_columns > max_columns:
        return f'DataFrame(shape={df.shape})'
    if max_rows is not None and num_lines > max_rows:
        df = df.head(3)
    s = llm_readable_to_csv(df, **_get_formatters(should_format))
    if num_lines > max_rows:
        s += f'\n... total {num_lines} rows'
    return s


def df_to_numerically_labeled_latex(df, should_format: bool = True, **kwargs):
    """
    Get latex representation of a DataFrame with numeric values labeled.
    Label the numeric values with @@<...>@@ - to allow converting to ReferenceableText.
    """
    return to_latex_with_value_format(df, **_get_formatters(should_format), **kwargs)
