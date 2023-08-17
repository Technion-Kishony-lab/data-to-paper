from functools import partial
from typing import Iterable, Dict, Callable, Optional

import pandas as pd
from pandas.core.frame import DataFrame

from dataclasses import dataclass, field

from data_to_paper.utils import dedent_triple_quote_str
from data_to_paper.utils.mutable import Flag
from ...run_context import BaseRunContext
from .dataframe_operations import DataframeOperation, ChangeSeriesDataframeOperation, DataframeOperations
from . import df_methods
from ...types import RunIssue, CodeProblem

METHOD_NAMES_TO_FUNCS = {
    '__init__': df_methods.__init__,
    '__setitem__': df_methods.__setitem__,
    '__getitem__': df_methods.__getitem__,
    '__delitem__': df_methods.__delitem__,
    '__str__': df_methods.__str__,
    'to_string': df_methods.to_string,
    'to_csv': df_methods.to_csv,
    'to_latex': df_methods.to_latex,
    'to_html': df_methods.raise_on_call,
    'to_json': df_methods.raise_on_call,
}


@dataclass
class DataFrameSeriesChange(Exception):
    """
    Exception that is raised when a data frame series is changed.
    """
    changed_series: str = None

    def __str__(self):
        return f'Changed series: {self.changed_series}'


@dataclass
class TrackDataFrames(BaseRunContext):
    """
    Context manager that tracks all the data frames that are created and their changes during the context.
    """
    data_frame_operations: DataframeOperations = None

    allow_dataframes_to_change_existing_series: Optional[bool] = True
    # True: allow changing existing series for all df
    # False: raise an exception when trying to change an existing series for all df
    # None: allow changing existing series for all df except for the ones that are created from a file

    enforce_saving_altered_dataframes: bool = False

    str_float_format: str = field(default_factory=lambda: df_methods.STR_FLOAT_FORMAT)

    df_creating_func_names_and_is_file: Iterable[str] = (
        ('read_csv', True),
        ('read_excel', True),
        ('read_json', True),
    )
    df_method_names_to_funcs: Dict[str, Callable] = field(default_factory=lambda: METHOD_NAMES_TO_FUNCS)

    _original_float_format: Optional[str] = None
    _df_creating_func_names_to_original_funcs: Optional[Dict[str, Callable]] = None
    _df_method_names_to_original_methods: Optional[Dict[str, Callable]] = None
    _prevent_recording_changes: Flag = field(default_factory=Flag)

    def _df_creating_func_override(self, *args, original_func=None, is_file=False, **kwargs):
        """
        Override for a dataframe creating function.
        Adds a `file_path` and a `created_by` attribute to the created dataframe.
        """
        with self._prevent_recording_changes.temporary_set(True):
            df = original_func(*args, **kwargs)
        if not isinstance(df, pd.DataFrame):
            return df
        if is_file:
            file_path = args[0] if len(args) > 0 else kwargs.get('filepath_or_buffer')
        else:
            file_path = None
        return pd.DataFrame(df, created_by=original_func.__name__, file_path=file_path)

    def _override_df_creating_funcs(self):
        """
        Hook all the dataframe creating functions so that they return a DataFrame with a `file_path` and a
        `created_by` attributes.
        """
        self._df_creating_func_names_to_original_funcs = {}
        for func_name, is_file in self.df_creating_func_names_and_is_file:
            original_func = getattr(pd, func_name)
            setattr(pd, func_name,
                    partial(self._df_creating_func_override, original_func=original_func, is_file=is_file))
            self._df_creating_func_names_to_original_funcs[func_name] = original_func

    def _de_override_df_creating_funcs(self):
        """
        De-hook all the dataframe creating functions.
        """
        for func_name, original_func in self._df_creating_func_names_to_original_funcs.items():
            setattr(pd, func_name, original_func)
        self._df_creating_func_names_to_original_funcs = None

    def _get_wrapped_method(self, new_method, original_method):
        """
        Wrap a method so that it has the original method as an argument and the `on_change` callback.
        """
        def wrapped_method(*args, **kwargs):
            return new_method(*args, original_method=original_method, on_change=self._on_change, **kwargs)
        return wrapped_method

    def _override_df_methods(self):
        """
        Override specified dataframe methods so that they report changes to the dataframe.
        As well as other enhancements.
        """
        self._df_method_names_to_original_methods = {}
        for method_name, new_method in self.df_method_names_to_funcs.items():
            original_method = getattr(DataFrame, method_name)
            wrapped_new_method = self._get_wrapped_method(new_method, original_method)
            setattr(DataFrame, method_name, wrapped_new_method)
            self._df_method_names_to_original_methods[method_name] = original_method

    def _de_override_df_methods(self):
        """
        De-hook all the dataframe methods.
        """
        for func_name, original_func in self._df_method_names_to_original_methods.items():
            setattr(DataFrame, func_name, original_func)
        self._df_method_names_to_original_methods = None

    def _override_float_format(self):
        """
        Override the float format.
        """
        if self.str_float_format:
            pd.set_option(f'display.float_format', self.str_float_format)
            self._original_float_format = pd.get_option('display.float_format')
        else:
            self._original_float_format = None

    def _de_override_float_format(self):
        """
        De-hook the float format.
        """
        if self._original_float_format:
            pd.set_option(f'display.float_format', self._original_float_format)
            self._original_float_format = None

    def _on_change(self, df, series_operation: DataframeOperation):
        if self._prevent_recording_changes:
            return
        if isinstance(series_operation, ChangeSeriesDataframeOperation):
            if self.allow_dataframes_to_change_existing_series is False \
                    or (self.allow_dataframes_to_change_existing_series is None and df.file_path is not None):
                raise DataFrameSeriesChange(changed_series=series_operation.series_name)
        self.dataframe_operations.append(series_operation)

    def _create_issues_for_unsaved_dataframes(self):
        if not self.enforce_saving_altered_dataframes:
            return
        dataframe_operations = self.dataframe_operations
        if dataframe_operations.get_read_changed_but_unsaved_ids():
            # Not all changed dataframes were saved to files.
            read_but_unsaved_filenames = dataframe_operations.get_read_filenames_from_ids(
                dataframe_operations.get_read_changed_but_unsaved_ids())
            self.issues.append(RunIssue(
                category='Any modified dataframe should be saved to a file',
                issue=dedent_triple_quote_str(f"""
                    Your code modifies, but doesn't save, some of the dataframes:
                    {read_but_unsaved_filenames}.
                    """),
                instructions=dedent_triple_quote_str("""
                    The code should use `to_csv` to save any modified dataframe in a new file \
                    in the same directory as the code.
                    """),
                comment='Not all modified dataframes were saved',
                code_problem=CodeProblem.MissingOutputFiles,
            ))

    def __enter__(self):
        self._override_df_creating_funcs()
        self._override_df_methods()
        self._override_float_format()
        self.dataframe_operations = DataframeOperations()
        return super().__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._de_override_float_format()
        self._de_override_df_methods()
        self._de_override_df_creating_funcs()
        self._create_issues_for_unsaved_dataframes()
        super().__exit__(exc_type, exc_val, exc_tb)
