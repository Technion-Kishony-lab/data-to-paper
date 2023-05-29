import pandas as pd

from functools import partial

from contextlib import contextmanager
from dataclasses import dataclass

from scientistgpt.utils.singleton import run_once

from .dataframe_operations import DataframeOperation, \
    ChangeSeriesDataframeOperation, \
    AddSeriesDataframeOperation, RemoveSeriesDataframeOperation, CreationDataframeOperation, DataframeOperations, \
    SeriesDataframeOperation, SaveDataframeOperation


@dataclass
class DataFrameSeriesChange(Exception):
    """
    Exception that is raised when a data frame series is changed.
    """
    changed_series: str = None

    def __str__(self):
        return f'Changed series: {self.changed_series}'


class ReportingDataFrame(pd.DataFrame):
    ALLOW_CHANGING_EXISTING_SERIES = True
    ON_CHANGE = None

    def __init__(self, *args, created_by: str = None, file_path: str = None, **kwargs):
        super().__init__(*args, **kwargs)

        self.created_by = created_by
        self.file_path = file_path
        self._notify_on_change(CreationDataframeOperation(
            id=id(self), created_by=created_by, file_path=file_path, columns=list(self.columns.values)))

    def __hash__(self):
        return hash(id(self))

    @staticmethod
    def set_on_change(on_change, allow_changing_existing_series=True):
        ReportingDataFrame.ALLOW_CHANGING_EXISTING_SERIES = allow_changing_existing_series
        ReportingDataFrame.ON_CHANGE = on_change

    def _notify_on_change(self, operation: DataframeOperation):
        if ReportingDataFrame.ON_CHANGE is not None:
            ReportingDataFrame.ON_CHANGE(self, operation)

    def __setitem__(self, key, value):
        operation_type = ChangeSeriesDataframeOperation if key in self else AddSeriesDataframeOperation
        if not self.ALLOW_CHANGING_EXISTING_SERIES and operation_type is ChangeSeriesDataframeOperation:
            raise DataFrameSeriesChange(changed_series=key)
        super().__setitem__(key, value)
        self._notify_on_change(operation_type(id=id(self), series_name=key))

    def __delitem__(self, key):
        super().__delitem__(key)
        self._notify_on_change(RemoveSeriesDataframeOperation(id=id(self), series_name=key))

    def __str__(self):
        # to avoid printing with [...] skipping columns
        return self.to_string()

    def to_csv(self, *args, **kwargs):
        result = super().to_csv(*args, **kwargs)
        file_path = args[0] if len(args) > 0 else kwargs.get('path_or_buf')
        self._notify_on_change(SaveDataframeOperation(
            id=id(self), file_path=file_path, columns=list(self.columns.values)))
        return result


pd.DataFrame = ReportingDataFrame


# NDFrame.to_csv = ReportingDataFrame.to_csv


DF_CREATING_FUNCTIONS = [
    'read_csv',
    'read_excel',
    'read_json',
]


def hook_func(*args, original_func=None, **kwargs):
    df = original_func(*args, **kwargs)
    file_path = args[0] if len(args) > 0 else kwargs.get('filepath_or_buffer')
    reporting_df = ReportingDataFrame(df, created_by=original_func.__name__, file_path=file_path)
    return reporting_df


@run_once
def hook_dataframe():
    """
    Hook all the dataframe creating functions so that they return a ReportingDataFrame instance.
    """
    for func_name in DF_CREATING_FUNCTIONS:
        original_func = getattr(pd, func_name)
        setattr(pd, func_name, partial(hook_func, original_func=original_func))


@contextmanager
def collect_created_and_changed_data_frames(allow_changing_existing_series=False) -> DataframeOperations:
    """
    Context manager that collects all the data frames that are created and their changes during the context.
    """
    hook_dataframe()
    dataframe_operations = DataframeOperations()

    def on_change(df, series_operation: SeriesDataframeOperation):
        dataframe_operations.append(series_operation)

    original_on_change = ReportingDataFrame.ON_CHANGE
    original_allow_changing_existing_series = ReportingDataFrame.ALLOW_CHANGING_EXISTING_SERIES

    ReportingDataFrame.set_on_change(on_change, allow_changing_existing_series)

    try:
        yield dataframe_operations
    finally:
        ReportingDataFrame.set_on_change(original_on_change, original_allow_changing_existing_series)
