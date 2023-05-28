import pandas as pd

from enum import Enum
from pathlib import Path
from functools import partial
from typing import List, NamedTuple, Dict, Tuple, Optional, Set

from contextlib import contextmanager
from dataclasses import dataclass

from scientistgpt.utils.singleton import run_once


@dataclass(frozen=True)
class BaseDataframeOperation:
    id: int


@dataclass(frozen=True)
class CreationDataframeOperation(BaseDataframeOperation):
    created_by: Optional[str]
    file_path: Optional[str]

    @property
    def filename(self):
        if self.file_path is None:
            return None
        return Path(self.file_path).name


class SeriesOperationType(Enum):
    ADD = 'add'
    CHANGE = 'change'
    DELETE = 'delete'


@dataclass(frozen=True)
class SeriesDataframeOperation(BaseDataframeOperation):
    operation_type: SeriesOperationType
    series_name: str


class DataframeOperations(List[BaseDataframeOperation]):
    pass

    def get_changed_dataframes(self) -> Set[int]:
        return {operation.id for operation in self if isinstance(operation, SeriesDataframeOperation)}


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
    ON_CREATION = None

    def __init__(self, *args, created_by: str = None, file_path: str = None, **kwargs):
        super().__init__(*args, **kwargs)

        self.created_by = created_by
        self.file_path = file_path
        if ReportingDataFrame.ON_CREATION is not None:
            ReportingDataFrame.ON_CREATION(self, CreationDataframeOperation(
                id(self), created_by=created_by, file_path=file_path))

    def __hash__(self):
        return hash(id(self))

    @classmethod
    def set_on_creation(cls, on_creation):
        ReportingDataFrame.ON_CREATION = on_creation

    @staticmethod
    def set_on_change(on_change, allow_changing_existing_series=True):
        ReportingDataFrame.ALLOW_CHANGING_EXISTING_SERIES = allow_changing_existing_series
        ReportingDataFrame.ON_CHANGE = on_change

    def _notify_on_change(self, operation_type: SeriesOperationType = None, series_name: str = None):
        if ReportingDataFrame.ON_CHANGE is not None:
            ReportingDataFrame.ON_CHANGE(self, SeriesDataframeOperation(
                id(self), operation_type=operation_type, series_name=series_name))

    def __setitem__(self, key, value):
        operation_type = SeriesOperationType.CHANGE if key in self else SeriesOperationType.ADD
        if not self.ALLOW_CHANGING_EXISTING_SERIES and operation_type == SeriesOperationType.CHANGE:
            raise DataFrameSeriesChange(changed_series=key)
        super().__setitem__(key, value)
        self._notify_on_change(operation_type=operation_type, series_name=key)

    def __delitem__(self, key):
        super().__delitem__(key)
        self._notify_on_change(operation_type=SeriesOperationType.DELETE, series_name=key)

    def __str__(self):
        # to avoid printing with [...] skipping columns
        return self.to_string()


pd.DataFrame = ReportingDataFrame


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


class DataFrameChanges:
    """
    Exception that is raised when a data frame is changed.
    """
    pass


@contextmanager
def collect_created_and_changed_data_frames(allow_changing_existing_series=False) -> DataframeOperations:
    """
    Context manager that collects all the data frames that are created and their changes during the context.
    """
    hook_dataframe()
    dataframe_operations = DataframeOperations()

    def on_creation(df, creation_operation: CreationDataframeOperation):
        dataframe_operations.append(creation_operation)

    def on_change(df, series_operation: SeriesDataframeOperation):
        dataframe_operations.append(series_operation)

    original_on_change = ReportingDataFrame.ON_CHANGE
    original_allow_changing_existing_series = ReportingDataFrame.ALLOW_CHANGING_EXISTING_SERIES

    ReportingDataFrame.set_on_change(on_change, allow_changing_existing_series)

    original_on_creation = ReportingDataFrame.ON_CREATION
    ReportingDataFrame.set_on_creation(on_creation)

    try:
        yield dataframe_operations
    finally:
        ReportingDataFrame.set_on_change(original_on_change, original_allow_changing_existing_series)
        ReportingDataFrame.set_on_creation(original_on_creation)

