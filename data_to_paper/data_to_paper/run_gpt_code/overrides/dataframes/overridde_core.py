from functools import partial

import pandas as pd
from pandas.core.frame import DataFrame

from data_to_paper.run_gpt_code.overrides.dataframes.df_methods.methods import STR_FLOAT_FORMAT
from data_to_paper.utils.singleton import run_once

from . import df_methods


RAISE_ON_CALL_FUNC_NAMES = ['to_html', 'to_json']


FUNC_NAMES_TO_FUNCS = {
    '__init__': df_methods.__init__,
    '__setitem__': df_methods.__setitem__,
    '__getitem__': df_methods.__getitem__,
    '__delitem__': df_methods.__delitem__,
    '__str__': df_methods.__str__,
    'to_string': df_methods.to_string,
    'to_csv': df_methods.to_csv,
    'to_latex': df_methods.to_latex,
}


def is_overridden(self):
    return True


@run_once
def override_core_ndframe():
    """
    Overrides the pandas DataFrame class to report changes in the data frame.
    """
    for func_name, func in FUNC_NAMES_TO_FUNCS.items():
        setattr(DataFrame, func_name, func)

    for func_name in RAISE_ON_CALL_FUNC_NAMES:
        setattr(DataFrame, func_name, partial(df_methods.raise_on_call, method_name=func_name))

    DataFrame.is_overridden = is_overridden

    if STR_FLOAT_FORMAT:
        pd.set_option(f'display.float_format', STR_FLOAT_FORMAT)
