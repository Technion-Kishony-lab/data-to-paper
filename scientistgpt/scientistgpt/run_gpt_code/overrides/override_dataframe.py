import functools
from typing import List

import pandas as pd

from contextlib import contextmanager
from dataclasses import dataclass

from scientistgpt.utils.singleton import run_once


@dataclass
class DataFrameSeriesChange(Exception):
    """
    Exception that is raised when a data frame series is changed.
    """
    changed_series: str = None

    def __str__(self):
        return f'Changed series: {self.changed_series}'


class ChangeReportingDataFrame(pd.DataFrame):
    ALLOW_CHANGING_EXISTING_SERIES = True
    ON_CHANGE = None

    def __hash__(self):
        return int(pd.util.hash_pandas_object(self).sum())

    @staticmethod
    def set_on_change(on_change, allow_changing_existing_series=True):
        ChangeReportingDataFrame.ALLOW_CHANGING_EXISTING_SERIES = allow_changing_existing_series
        ChangeReportingDataFrame.ON_CHANGE = on_change

    def _notify_on_change(self):
        if ChangeReportingDataFrame.ON_CHANGE is not None:
            ChangeReportingDataFrame.ON_CHANGE(self)

    def __setitem__(self, key, value):
        if not self.ALLOW_CHANGING_EXISTING_SERIES and key in self:
            raise DataFrameSeriesChange(changed_series=key)
        super().__setitem__(key, value)
        self._notify_on_change()

    def __delitem__(self, key):
        super().__delitem__(key)
        self._notify_on_change()

    def __str__(self):
        return self.to_string()


pd.DataFrame = ChangeReportingDataFrame


DF_CREATING_FUNCTIONS = [
    'read_csv',
    'read_excel',
    'read_json',
]


def hook_func(*args, original_func=None, **kwargs):
    df = original_func(*args, **kwargs)
    return ChangeReportingDataFrame(df)


@run_once
def hook_dataframe():
    """
    Hook all the dataframe creating functions so that they return a ChangeReportingDataFrame instance.
    """
    for func_name in DF_CREATING_FUNCTIONS:
        original_func = getattr(pd, func_name)
        setattr(pd, func_name, functools.partial(hook_func, original_func=original_func))


@contextmanager
def collect_changed_data_frames(allow_changing_existing_series=False) -> List[ChangeReportingDataFrame]:
    """
    Context manager that collects all the data frames that were changed during the context.
    """
    hook_dataframe()
    changed_data_frames = []

    def on_df_change(df):
        changed_data_frames.append(df)

    original_on_change = ChangeReportingDataFrame.ON_CHANGE
    original_allow_changing_existing_series = ChangeReportingDataFrame.ALLOW_CHANGING_EXISTING_SERIES

    ChangeReportingDataFrame.set_on_change(on_df_change, allow_changing_existing_series)

    try:
        yield changed_data_frames
    finally:
        ChangeReportingDataFrame.set_on_change(original_on_change, original_allow_changing_existing_series)
