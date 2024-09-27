from copy import copy
from functools import wraps
from typing import Iterable, Dict, Callable, Optional, Tuple, List, Type

import pandas as pd

from pandas.core.frame import DataFrame

from dataclasses import dataclass, field

from pandas.core.indexing import _LocationIndexer

from data_to_paper.text import dedent_triple_quote_str
from data_to_paper.utils.mutable import Flag
from ...base_run_contexts import RunContext
from .dataframe_operations import DataframeOperation, ChangeSeriesDataframeOperation, DataframeOperations, \
    CreationDataframeOperation
from . import df_methods
from ...run_issues import CodeProblem, RunIssue

CLS_METHOD_NAMES_NEW_METHODS = [
    (DataFrame, '__init__', df_methods.__init__),
    (DataFrame, '__setitem__', df_methods.__setitem__),
    (DataFrame, '__getitem__', df_methods.__getitem__),
    (DataFrame, '__delitem__', df_methods.__delitem__),
    (DataFrame, '__str__', df_methods.__str__),
    (DataFrame, 'to_string', df_methods.to_string),
    (DataFrame, 'to_csv', df_methods.to_csv),
    (DataFrame, 'to_latex', df_methods.raise_on_call),
    (DataFrame, 'to_json', df_methods.raise_on_call),
    (_LocationIndexer, '__getitem__', df_methods.__LocationIndexer__get_item__),
]


@dataclass
class DataFrameSeriesChange(RunIssue):
    """
    Exception that is raised when a data frame series is changed.
    """
    changed_series: str = None
    category: str = 'Good coding practices: Dataframe series change'
    issue: str = 'Your code changes the series "{changed_series}" of your dataframe.\n' \
                 'This could lead to confusion and errors.'
    instructions: str = 'Instead of changing an existing dataframe series, please create a new series, and give it a ' \
                        'new sensible name.'
    code_problem: CodeProblem = CodeProblem.RuntimeError
    comment: str = 'Code modifies dataframe series'


@dataclass
class TrackDataFrames(RunContext):
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
        ('read_pickle', True),
        ('read_csv', True),
        ('read_excel', True),
        ('read_json', True),
    )
    cls_method_names_new_methods: List[Tuple[Type, str, Callable]] = \
        field(default_factory=lambda: CLS_METHOD_NAMES_NEW_METHODS)

    _original_float_format: Optional[str] = None
    _df_creating_func_names_to_original_funcs: Optional[Dict[str, Callable]] = None
    _cls_method_names_original_methods: Optional[List[Tuple[Type, str, Callable]]] = None
    _prevent_recording_changes: Flag = field(default_factory=Flag)

    def _df_creating_func_override(self, *args, original_method=None, is_file=False, on_change=None, **kwargs):
        """
        Override for a dataframe creating function.
        Adds a `file_path` and a `created_by` attribute to the created dataframe.
        """
        with self._prevent_recording_changes.temporary_set(True):
            df = original_method(*args, **kwargs)
        if not isinstance(df, pd.DataFrame):
            return df

        if is_file:
            file_path = args[0] if len(args) > 0 else kwargs.get('filepath_or_buffer')
        else:
            file_path = None
        created_by = original_method.__name__
        if isinstance(df, pd.DataFrame):
            df.created_by = created_by
            df.file_path = file_path
            on_change(df, CreationDataframeOperation(
                id=id(df), created_by=created_by, file_path=file_path, columns=copy(df.columns.values)))
        return df

    def _override_df_creating_funcs(self):
        """
        Hook all the dataframe creating functions so that they return a DataFrame with a `file_path` and a
        `created_by` attributes.
        """
        self._df_creating_func_names_to_original_funcs = {}
        for func_name, is_file in self.df_creating_func_names_and_is_file:
            original_func = getattr(pd, func_name)
            assert hasattr(pd, func_name), f"pd does not have a method {func_name}"
            wrapped_new_method = self._get_wrapped_new_method(
                self._df_creating_func_override, original_func, is_file=is_file)
            setattr(pd, func_name, wrapped_new_method)
            self._df_creating_func_names_to_original_funcs[func_name] = original_func

    def _de_override_df_creating_funcs(self):
        """
        De-hook all the dataframe creating functions.
        """
        for func_name, original_func in self._df_creating_func_names_to_original_funcs.items():
            setattr(pd, func_name, original_func)
        self._df_creating_func_names_to_original_funcs = None

    def _get_wrapped_new_method(self, new_method, original_method, **kwargs):
        """
        Wrap a method so that it has the original method as an argument and the `on_change` callback.
        """
        @wraps(original_method)
        def wrapped_new_method(*args, **k):
            return new_method(*args, original_method=original_method, on_change=self._on_change, **k, **kwargs)
        wrapped_new_method.wrapper_of = original_method
        return wrapped_new_method

    def _override_df_methods(self):
        """
        Override specified dataframe methods so that they report changes to the dataframe.
        As well as other enhancements.
        """
        self._cls_method_names_original_methods = []
        for cls, method_name, new_method in self.cls_method_names_new_methods:
            original_method = getattr(cls, method_name)
            wrapped_new_method = self._get_wrapped_new_method(new_method, original_method)
            setattr(cls, method_name, wrapped_new_method)
            self._cls_method_names_original_methods.append((cls, method_name, original_method))

    def _de_override_df_methods(self):
        """
        De-hook all the dataframe methods.
        """
        for cls, method_name, original_method in self._cls_method_names_original_methods:
            setattr(cls, method_name, original_method)
        self._cls_method_names_original_methods = None

    def _override_float_format(self):
        """
        Override the float format.
        """
        if self.str_float_format:
            self._original_float_format = pd.get_option('display.float_format')
            pd.set_option(f'display.float_format', self.str_float_format)
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
        if isinstance(series_operation, ChangeSeriesDataframeOperation) and self._is_called_from_user_script(5):
            if self.allow_dataframes_to_change_existing_series is False \
                    or (self.allow_dataframes_to_change_existing_series is None and df.file_path is not None):
                self.issues.append(DataFrameSeriesChange.from_current_tb(changed_series=series_operation.series_name))
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
                category='Coding good practice: Any modified dataframe should be saved to a file',
                issue=dedent_triple_quote_str(f"""
                    Your code modifies, but doesn't save, some of the dataframes:
                    {read_but_unsaved_filenames}.
                    """),
                instructions=dedent_triple_quote_str("""
                    The code should use `to_csv` to save any modified dataframe in a new file \t
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
        return super().__exit__(exc_type, exc_val, exc_tb)
