"""
All rule-based checks of calls to `df_to_figure` and `df_to_latex` are defined here.

The checks are divided into categories:

For the analysis step:
1. Syntax checks: checks for correct syntax of the calls to `df_to_figure` and `df_to_latex`.
2. Content checks (analysis): Check for content of the dataframes created in the analysis step.

For the display-item step, we further add:
3. Continuity checks: Check that the df are created from the output of the analysis step.
4. Content checks (display-item): Check for content of the dataframes created in the display-item step.
5. Compilation checks: Run compilation and check for errors and wide tables.
6. Annotation checks: Check for annotations (like the labels of the df, and note, glossary, and caption).


Note: check methods must start with `check_`.
Use CHOICE_OF_CHECKS to specify the order and which checks to run.

For transparency, all check_ methods must be specified in CHOICE_OF_CHECKS.
This is automatically asserted by the BaseChecker class.
"""


from dataclasses import dataclass, field
import re
from typing import Dict, Union, Optional, List, Any, Tuple, Type, ClassVar, Callable

import numpy as np
import pandas as pd
from pathlib import Path

from data_to_paper.env import DEBUG_MODE
from data_to_paper.latex.exceptions import BaseLatexProblemInCompilation
from data_to_paper.latex.latex_doc import LatexDocument
from data_to_paper.llm_coding_utils import df_to_latex, df_to_figure, ALLOWED_PLOT_KINDS, DF_ALLOWED_VALUE_TYPES
from data_to_paper.llm_coding_utils.consts import DF_ALLOWED_COLUMN_TYPES
from data_to_paper.llm_coding_utils.df_to_figure import run_create_fig_for_df_to_figure_and_get_axis_parameters
from data_to_paper.llm_coding_utils.matplotlib_utils import AxisParameters
from data_to_paper.run_gpt_code.base_run_contexts import RegisteredRunContext
from data_to_paper.run_gpt_code.overrides.dataframes.df_with_attrs import InfoDataFrameWithSaveObjFuncCall

from data_to_paper.text import dedent_triple_quote_str
from data_to_paper.utils.check_type import raise_on_wrong_func_argument_types, name_of_type
from data_to_paper.utils.dataframe import extract_df_row_labels, extract_df_column_labels, extract_df_axes_labels
from data_to_paper.utils.nice_list import NiceList
from data_to_paper.utils.numerics import is_lower_eq

from data_to_paper.research_types.hypothesis_testing.env import get_max_rows_and_columns, MAX_BARS
from data_to_paper.run_gpt_code.overrides.dataframes.utils import df_to_llm_readable_csv
from data_to_paper.run_gpt_code.overrides.pvalue import is_p_value, PValue, is_containing_p_value, is_only_p_values, \
    OnStrPValue, OnStr
from data_to_paper.run_gpt_code.run_issues import CodeProblem, RunIssue, RunIssues
from .abbreviations import is_unknown_abbreviation
from .utils import is_non_integer_numeric, _find_longest_labels_in_index, \
    _find_longest_labels_in_columns_relative_to_content


@dataclass
class BaseChecker:

    issues: RunIssues = field(default_factory=RunIssues)
    intermediate_results: Dict[str, Any] = field(default_factory=dict)
    stop_after_first_issue: bool = False

    def _append_issue(self, category: str = None, item: str = None, issue: str = '', instructions: str = '',
                      code_problem: CodeProblem = None, forgive_after: Optional[int] = None):
        self.issues.append(RunIssue(
            category=category,
            item=item,
            issue=issue,
            instructions=instructions,
            code_problem=code_problem,
            forgive_after=forgive_after,
        ))

    def _automatically_get_all_check_methods(self):
        return [getattr(type(self), method_name) for method_name in dir(self) if method_name.startswith('check')]

    def _assert_if_provided_choice_of_checks_include_all_check_methods(self):
        if self.CHOICE_OF_CHECKS is not None:
            for check_method in self._automatically_get_all_check_methods():
                assert check_method in self.CHOICE_OF_CHECKS, f'Missing check method: {check_method.__name__}'

    def _get_checks_to_run(self):
        if self.CHOICE_OF_CHECKS is None:
            return self._automatically_get_all_check_methods()
        return [check for check, should_check in self.CHOICE_OF_CHECKS.items() if should_check]

    def _run_checks(self):
        self._assert_if_provided_choice_of_checks_include_all_check_methods()
        for check in self._get_checks_to_run():
            num_issues_before = len(self.issues)
            should_stop = check(self)
            num_created_issues = len(self.issues) - num_issues_before
            if should_stop and not num_created_issues:
                assert False, f'Check {check.__name__} returned True, but no issues were created.'
            if DEBUG_MODE:
                print(f'Check "{check.__name__}" created {num_created_issues} issues.')
            if self.issues and (self.stop_after_first_issue or should_stop):
                break

    def run_checks(self) -> Tuple[RunIssues, Dict[str, Any]]:
        self._run_checks()
        return self.issues, self.intermediate_results

    CHOICE_OF_CHECKS: ClassVar[Optional[Dict[Callable, bool]]] = None


@dataclass
class ChainChecker(BaseChecker):
    checkers: List[BaseChecker] = None
    stop_after_first_issue: bool = True

    def _run_checks(self):
        for checker in self.checkers:
            checker.intermediate_results.update(self.intermediate_results)
            issues, intermediate_results = checker.run_checks()
            self.issues.extend(issues)
            self.intermediate_results.update(intermediate_results)
            non_forgivable_issues = [issue for issue in self.issues if issue.forgive_after is None]
            if non_forgivable_issues and self.stop_after_first_issue:
                break


def create_and_run_chain_checker(checkers: List[Type[BaseChecker]], stop_after_first_issue: bool = True, **kwargs
                                 ) -> Tuple[RunIssues, Dict[str, Any]]:
    chain_checker = ChainChecker(checkers=[checker(**kwargs) for checker in checkers],  # type: ignore
                                 stop_after_first_issue=stop_after_first_issue)
    return chain_checker.run_checks()


@dataclass
class BaseDfChecker(BaseChecker):
    func: Callable = None
    df: pd.DataFrame = None
    filename: str = None
    kwargs: dict = field(default_factory=dict)

    output_folder: Optional[Path] = None  # where compiled figures and tables are saved
    latex_document: Optional[LatexDocument] = None

    DEFAULT_CATEGORY: ClassVar[str] = None
    DEFAULT_CODE_PROBLEM: ClassVar[CodeProblem] = None

    NAMES_OF_KWARGS_FOR_LATEX = ['caption', 'label', 'note', 'glossary']

    def _append_issue(self, category: str = None, item: str = None, issue: str = '', instructions: str = '',
                      code_problem: CodeProblem = None, forgive_after: Optional[int] = None):
        category = self.DEFAULT_CATEGORY if category is None else category
        code_problem = self.DEFAULT_CODE_PROBLEM if code_problem is None else code_problem
        item = self.filename if item is None else item
        super()._append_issue(category=category, item=item, issue=issue, instructions=instructions,
                              code_problem=code_problem, forgive_after=forgive_after)

    def _run_and_get_result_and_exception(self, **additional_kwargs) -> Tuple[Any, Optional[Exception]]:
        try:
            result = self.func(self.df, self.filename, **self.kwargs, **additional_kwargs)
        except Exception as e:
            return None, e
        return result, None

    @property
    def func_name(self):
        if self.func is None:
            return None
        return self.func.__name__

    @property
    def is_figure(self):
        return self.func_name == 'df_to_figure'

    @property
    def table_or_figure(self):
        return 'figure' if self.is_figure else 'table'

    @property
    def index(self) -> bool:
        if self.is_figure:
            return self.kwargs.get('use_index', True) and self.x is None
        else:
            return self.kwargs.get('index', True)

    def get_x_labels(self):
        if self.is_figure:
            if self.index:
                return self.df.index
            x = self.x
            if x is None:
                return np.array(range(self.df.shape[0]))
            return self.df[x]
        else:
            if self.index:
                return self.df.index
            # if the index is not used, it is the first column that behaves as the index:
            return self.df.iloc[:, 0]

    def get_y_labels(self):
        if self.is_figure:
            y, _, _, _ = self.get_xy_err_ci_p_value('y', as_list=True)
            return y
        return self.df.columns

    @property
    def note(self) -> Optional[str]:
        return self.kwargs.get('note', None)

    @property
    def glossary(self) -> Optional[Dict[str, str]]:
        return self.kwargs.get('glossary', None)

    @property
    def caption(self) -> Optional[str]:
        return self.kwargs.get('caption', None)

    @property
    def kind(self) -> Optional[str]:
        return self.kwargs.get('kind', 'bar')

    @property
    def x(self) -> Optional[str]:
        return self.kwargs.get('x', None)

    @property
    def y(self) -> Optional[Union[str, List[str]]]:
        return self.kwargs.get('y', None)

    @property
    def yerr(self) -> Optional[Union[str, List[str]]]:
        return self.kwargs.get('yerr', None)

    @property
    def xerr(self) -> Optional[str]:
        return self.kwargs.get('yerr', None)

    @property
    def y_ci(self) -> Optional[Union[str, List[str]]]:
        return self.kwargs.get('y_ci', None)

    @property
    def x_ci(self) -> Optional[str]:
        return self.kwargs.get('x_ci', None)

    @property
    def y_p_value(self) -> Optional[Union[str, List[str]]]:
        return self.kwargs.get('y_p_value', None)

    @property
    def x_p_value(self) -> Optional[str]:
        return self.kwargs.get('x_p_value', None)

    def get_xlabel(self):
        label = self.kwargs.get('xlabel', None)
        if label is not None:
            return label
        return self.x

    def get_ylabel(self):
        label = self.kwargs.get('ylabel', None)
        if label is not None:
            return label
        if not isinstance(self.y, list):
            return self.y
        return None

    @staticmethod
    def _convert_to_list(value, flatten):
        if value is None:
            as_list = []
        else:
            as_list = [value] if isinstance(value, str) else value

        if not flatten:
            return as_list

        flatten_list = []
        for item in as_list:
            if isinstance(item, tuple):
                flatten_list.extend(item)
            else:
                flatten_list.append(item)
        return flatten_list

    def get_xy_err_ci_p_value(self, x_or_y: str, as_list=False, flatten=False):

        xy = getattr(self, x_or_y)
        err = getattr(self, f'{x_or_y}err')
        ci = getattr(self, f'{x_or_y}_ci')
        p_value = getattr(self, f'{x_or_y}_p_value')
        if as_list:
            xy = self._convert_to_list(xy, flatten)
            err = self._convert_to_list(err, flatten)
            ci = self._convert_to_list(ci, flatten)
            p_value = self._convert_to_list(p_value, flatten)
        return xy, err, ci, p_value

    @property
    def kwargs_for_plot(self):
        """
        Remove the kwargs for latex from the kwargs.
        """
        return {key: value for key, value in self.kwargs.items() if key not in self.NAMES_OF_KWARGS_FOR_LATEX}

    CHOICE_OF_CHECKS = {}


""" SYNTAX """


@dataclass
class SyntaxDfChecker(BaseDfChecker):
    """
    Checks that do not depend on the content of df.
    """
    DEFAULT_CATEGORY = 'Checking df_to_figure/df_to_latex for call syntax'
    DEFAULT_CODE_PROBLEM = CodeProblem.OutputFileCallingSyntax

    def check_argument_types(self):
        try:
            raise_on_wrong_func_argument_types(df_to_latex, self.df, self.filename, **self.kwargs)
        except TypeError as e:
            self._append_issue(issue=str(e))
            return True  # No more checks. Further checks may create errors.

    def check_filename(self):
        """
        Check if the filename of in the format `df_<alphanumeric>`.
        """
        pattern = r'^df_[a-zA-Z0-9_]+$'
        if not re.match(pattern=pattern, string=self.filename):
            self._append_issue(
                issue=f'Filenames of tables and figures should be in the format `df_<alphanumeric>` (without .ext), '
                      f'but got "{self.filename}".',
            )

    def check_no_label(self):
        if self.kwargs.get('label', None):
            self._append_issue(
                issue=f'The `label` argument should not be used in `df_to_figure` or `df_to_latex`; '
                      f'It is automatically generated from the filename.',
                instructions='Please remove the `label` argument.',
            )

    CHOICE_OF_CHECKS = BaseDfChecker.CHOICE_OF_CHECKS | {
        check_argument_types: True,
        check_filename: True,
        check_no_label: True,
    }


@dataclass
class TableSyntaxDfChecker(SyntaxDfChecker):
    func: Callable = df_to_latex

    def check_that_index_is_true(self):
        if not self.index:
            self._append_issue(
                issue='Do not call `df_to_latex` with `index=False`.',
                instructions=dedent_triple_quote_str("""
                    Please revise the code making sure all tables are created with `index=True`, \t
                    and that the index is meaningful.
                    """)
            )

    def check_column_arg_is_not_used(self):
        if 'columns' in self.kwargs:
            self._append_issue(
                issue='Do not use the `columns` argument in `df_to_latex`.',
                instructions='If you want to drop columns, do it before calling `df_to_latex`.',
            )

    CHOICE_OF_CHECKS = SyntaxDfChecker.CHOICE_OF_CHECKS | {
        check_that_index_is_true: True,
        check_column_arg_is_not_used: True,
    }


@dataclass
class FigureSyntaxDfChecker(SyntaxDfChecker):
    func: Callable = df_to_figure

    def check_kind_arg(self):
        """
        Check if the plot kind is one of the allowed plot kinds.
        """
        if 'kind' not in self.kwargs:
            self._append_issue(
                issue=f'Plot `kind` is not specified.',
                instructions=f'Please explicitly specify the `kind` argument. available options are:\n'
                             f'{ALLOWED_PLOT_KINDS}.',
            )
        elif self.kind not in ALLOWED_PLOT_KINDS:
            self._append_issue(
                issue=f'Plot kind "{self.kind}" is not supported.',
                instructions=f'Only use these kinds: {ALLOWED_PLOT_KINDS}.',
            )

    def check_y_arg(self):
        if self.y is None:
            self._append_issue(
                issue=f'No y values are specified.',
                instructions='Please use the `y` argument to specify the columns to be plotted.',

            )

    def check_yerr_arg(self):
        if self.yerr is not None:
            self._append_issue(
                issue=f'Do not use the `yerr` argument in `df_to_figure`.',
                instructions='Instead, directly indicate the confidence intervals using the `y_ci` argument.',
            )

    def check_x_p_value_arg(self):
        if self.x_p_value:
            self._append_issue(
                issue='The `x_p_value` argument is not supported.',
                instructions='Please use the `y_p_value` argument instead.',
            )

    def check_y_p_value_arg(self):
        # This check i obsolete, because of `check_x_p_value_arg`.
        if self.x_p_value is not None and self.y_p_value is not None:
            self._append_issue(
                issue='Both `x_p_value` and `y_p_value` are set.',
                instructions='Please use only one of them.',
            )
            return

    CHOICE_OF_CHECKS = SyntaxDfChecker.CHOICE_OF_CHECKS | {
        check_kind_arg: True,
        check_y_arg: True,
        check_yerr_arg: True,
        check_x_p_value_arg: True,
        check_y_p_value_arg: True,
    }


""" CONTENT FOR ANALYSIS STEP """


@dataclass
class BaseContentDfChecker(BaseDfChecker):
    stop_after_first_issue: bool = True

    prior_dfs: Dict[str, pd.DataFrame] = field(default_factory=dict)

    ALLOWED_VALUE_TYPES = DF_ALLOWED_VALUE_TYPES + (PValue,)
    ALLOWED_COLUMN_AND_INDEX_TYPES = {'columns': DF_ALLOWED_COLUMN_TYPES, 'index': DF_ALLOWED_VALUE_TYPES}
    ALLOW_MULTI_INDEX_FOR_COLUMN_AND_INDEX = {'columns': True, 'index': True}

    DEFAULT_CATEGORY = 'Checking content of created dfs'
    DEFAULT_CODE_PROBLEM = CodeProblem.OutputFileContentA

    def _get_x_values(self):
        if self.is_figure:
            x = self.x
            if x is None:
                return self.df.index
            return self.df[x]
        else:
            if self.index:
                return self.df.index
            # if the index is not used, it is the first column that behaves as the index:
            return self.df.iloc[:, 0]

    def _get_max_rows_and_columns(self):
        return get_max_rows_and_columns(self.is_figure, kind=self.kind, to_show=False)


@dataclass
class DfContentChecker(BaseContentDfChecker):
    VALUES_CATEGORY = 'Problem with df values'
    INDEX_COLUMN_CATEGORY = 'Problem with df index/columns'
    SIZE_CATEGORY = 'Too large df'

    def get_relevant_part_of_df(self):
        """
        Get the part of the df that is relevant for the checks.
        """
        if not self.is_figure:
            return self.df
        y, yerr, y_ci, y_p_value = self.get_xy_err_ci_p_value('y', as_list=True, flatten=True)
        x, xerr, x_ci, x_p_value = self.get_xy_err_ci_p_value('x', as_list=True, flatten=True)
        return self.df[y + yerr + y_ci + y_p_value + x + xerr + x_ci + x_p_value]

    def check_df_headers_type(self):
        for column_or_index in ['columns', 'index']:
            headers = getattr(self.df, column_or_index)

            # Check if the headers are a multi-index and if it is allowed:
            if not self.ALLOW_MULTI_INDEX_FOR_COLUMN_AND_INDEX[column_or_index] and isinstance(headers, pd.MultiIndex):
                self._append_issue(
                    category=self.INDEX_COLUMN_CATEGORY,
                    issue=f"Your dataframe has a multi-index for the {column_or_index}.",
                    instructions=f"Please make sure the df has a single-level {column_or_index}.",
                )
                continue

            # Check if the headers are of the allowed types:
            allowed_types = self.ALLOWED_COLUMN_AND_INDEX_TYPES[column_or_index]
            unsupported_headers = self._get_df_headers_of_unsupported_types(headers, allowed_types)
            if unsupported_headers:
                nice_list = NiceList((f"`{repr(header)}`  (type `{name_of_type(type(header))}` is not allowed)"
                                      for header in unsupported_headers), separator='\n')
                nice_allowed_types = [name_of_type(allowed_type) for allowed_type in allowed_types]
                self._append_issue(
                    category=self.INDEX_COLUMN_CATEGORY,
                    issue=f"Your df has {column_or_index} headers of unsupported types:\n{nice_list}.",
                    instructions=f"The df {column_or_index} headers should be only of these types: "
                                 f"{nice_allowed_types}.",
                )

    def _check_if_df_within_df(self) -> bool:
        for value in self.df.values.flatten():
            if isinstance(value, (pd.Series, pd.DataFrame)):
                self._append_issue(
                    category=self.VALUES_CATEGORY,
                    issue=f"Something wierd in your dataframe. Iterating over df.values.flatten() "
                          f"returned a `{type(value).__name__}` object.",
                )
                return True
        return False

    def check_df_value_types(self):
        """
        Check if the dataframe has only allowed value types.
        """
        if self._check_if_df_within_df():
            return
        un_allowed_type_names = {f'{type(value).__name__}' for value in self.df.values.flatten()
                                 if not isinstance(value, self.ALLOWED_VALUE_TYPES)}
        if un_allowed_type_names:
            self._append_issue(
                category=self.VALUES_CATEGORY,
                issue=f"Your dataframe contains values of types {sorted(un_allowed_type_names)} which are not allowed.",
                instructions=f"Please make sure the saved dataframes have only numeric, str, bool, or tuple values.",
            )

    def check_df_for_nan_values(self):
        """
        Check if the df has NaN values or PValue with value of nan
        """
        relevant_df = self.get_relevant_part_of_df()
        df_with_raw_pvalues = relevant_df.applymap(lambda v: v.value if is_p_value(v) else v)
        isnull = pd.isnull(df_with_raw_pvalues)
        num_nulls = isnull.sum().sum()
        if num_nulls > 0:
            issue_text = f'Note that the df has {num_nulls} NaN value(s).'
            if len(isnull) < 20:
                issue_text += f'\nHere is the `isnull` of the df:'
            else:
                # show only the first 10 rows with NaN values:
                isnull = self.df[isnull.any(axis=1)].head(10)
                issue_text += f'\nHere are some example lines with NaN values:'
            issue_text += f'\n```\n{df_to_llm_readable_csv(isnull)}\n```\n'
            instructions = \
                f"Please revise the code to avoid NaN values in the created {self.table_or_figure}."
            if not self.is_figure:
                instructions += \
                    "\nIf the NaNs are legit and stand for missing values: replace them with the string '-'.\n" \
                    "Otherwise, if they are computational errors, please revise the code to fix it."
            self._append_issue(
                category=self.VALUES_CATEGORY,
                issue=issue_text,
                instructions=instructions
            )

    @staticmethod
    def _get_df_headers_of_unsupported_types(headers: Union[pd.MultiIndex, pd.Index], allowed_types: Tuple[Type]
                                             ) -> List[Any]:
        """
        Find any headers of the dataframe are int, str, or bool.
        """
        if isinstance(headers, pd.MultiIndex):
            headers = [label for level in range(headers.nlevels) for label in headers.get_level_values(level)]
        return [header for header in headers if not isinstance(header, allowed_types)]

    @staticmethod
    def _is_index_a_range(index, max_allowed_range: int = 2):
        num_rows = len(index)
        return not isinstance(index, pd.MultiIndex) \
            and list(index) == list(range(num_rows)) and pd.api.types.is_integer_dtype(index.dtype) \
            and num_rows > max_allowed_range

    CHOICE_OF_CHECKS = BaseDfChecker.CHOICE_OF_CHECKS | {
        check_df_headers_type: True,
        check_df_for_nan_values: True,
        check_df_value_types: True,
    }


@dataclass
class TableDfContentChecker(DfContentChecker):
    func: Callable = df_to_latex

    OVERLAYING_VALUES_CATEGORY = 'Overlapping values'
    DF_DISPLAY_CATEGORY = 'The df looks like a df.describe() table, not a scientific table'

    MAX_ROWS_ALLOWED_FOR_RANGE_AS_INDEX = 2

    def check_df_is_a_result_of_describe(self):
        """
        Check if the table is a df.describe() table
        """
        description_labels = ('mean', 'std', 'min', '25%', '50%', '75%', 'max')
        if set(description_labels).issubset(self.df.columns) or set(description_labels).issubset(self.df.index):
            self._append_issue(
                category=self.DF_DISPLAY_CATEGORY,
                issue=f'The df includes mean, std, as well as quantiles and min/max values.',
                instructions=dedent_triple_quote_str("""
                    Note that in scientific tables, it is not customary to include quantiles, or min/max values, \t
                    especially if the mean and std are also included.
                    Please revise the code so that the tables only include scientifically relevant statistics.
                    """),
                forgive_after=3,
            )

    def check_df_index_is_a_range(self):
        """
        Check if the index of the dataframe is just a numeric range.
        """
        if not self.index:
            return
        num_rows = self.df.shape[0]
        if self._is_index_a_range(self.df.index, self.MAX_ROWS_ALLOWED_FOR_RANGE_AS_INDEX):
            self._append_issue(
                category=self.INDEX_COLUMN_CATEGORY,
                issue=dedent_triple_quote_str(f"""
                    The function `df_to_latex` uses the index as the row labels.
                    But, the index of df "{self.filename}" is just a range from 0 to {num_rows - 1}.
                    """),
                instructions=dedent_triple_quote_str(f"""
                    Please revise the code making sure the figure is built with an index that represents meaningful \t
                    numeric data. Or, for categorical data, the index should be a list of strings.

                    Note: labeling row with sequential numbers is not common in scientific tables. \t
                    But, if you are sure that starting each row with a sequential number is really what you want, \t
                    then convert it from int to strings, so that it is clear that it is not a mistake.
                    """),
            )

    def check_df_for_repeated_values(self):
        """
        # Check if the table contains the same values in multiple cells
        """
        df_values = [v for v in self.df.values.flatten() if is_non_integer_numeric(v)]
        if len(df_values) != len(set(df_values)):
            # Find the positions of the duplicated values:
            duplicated_values = [v for v in df_values if df_values.count(v) > 1]
            example_value = duplicated_values[0]
            duplicated_value_positions = np.where(self.df.values == example_value)
            duplicated_value_positions = list(zip(*duplicated_value_positions))
            duplicated_value_positions = [f'({row}, {col})' for row, col in duplicated_value_positions]
            duplicated_value_positions = ', '.join(duplicated_value_positions)

            self._append_issue(
                category=self.OVERLAYING_VALUES_CATEGORY,
                issue=f'Note that the df "{self.filename}" includes the same values in multiple cells.\n'
                      f'For example, the value {example_value} appears in the following cells:\n'
                      f'{duplicated_value_positions}.',
                instructions=dedent_triple_quote_str("""
                    Is this perhaps a mistake, please revise the code so that the df does not repeat the same values \t
                    in multiple cells.
                    Otherwise, please just add a comment in the codee explaining why the same value might be repeated.
                    """),
                forgive_after=1,
            )

    def check_df_for_repeated_values_in_prior_dfs(self):
        """
        Check if the df numeric values overlap with values in prior dfs
        """
        if not self.prior_dfs:
            return
        df_values = [v for v in self.df.values.flatten() if is_non_integer_numeric(v)]
        for prior_name, prior_table in self.prior_dfs.items():
            if prior_table is self.df:
                continue
            prior_table_values = [v for v in prior_table.values.flatten() if is_non_integer_numeric(v)]
            if any(value in prior_table_values for value in df_values):
                self._append_issue(
                    category=self.OVERLAYING_VALUES_CATEGORY,
                    issue=f'Table "{self.filename}" includes values that overlap with values in table "{prior_name}".',
                    instructions=dedent_triple_quote_str("""
                        In scientific tables, it is not customary to include the same values in multiple tables.
                        Please revise the code so that each table include its own unique data.
                        """),
                    forgive_after=1,
                )

    def check_df_size(self):
        """
        Check if the df has too many columns or rows
        """
        shape = self.df.shape
        max_rows_and_columns = self._get_max_rows_and_columns()
        if is_lower_eq(shape[0], max_rows_and_columns[0]) and is_lower_eq(shape[1], max_rows_and_columns[1]):
            return
        max_rows, max_columns = max_rows_and_columns
        instructions = dedent_triple_quote_str(f"""
            Please revise the code so that df of created Tables \t
            have a maximum of {max_rows} rows and {max_columns} columns.
            Note that simply trimming the data is typically not a good solution.
            You might instead consider a different representation/organization of the table.
            Or, consider representing the data as a figure.
            """)
        if is_lower_eq(shape[0], max_rows_and_columns[1]) and is_lower_eq(shape[1], max_rows_and_columns[0]):
            instructions += "\nYou might also want to consider transposing the df (df = df.T)."
        for ax, rows_or_columns in enumerate(('rows', 'columns')):
            if not is_lower_eq(shape[ax], max_rows_and_columns[ax]):
                self._append_issue(
                    category=self.SIZE_CATEGORY,
                    issue=f'This table has {shape[ax]} {rows_or_columns}, which is too many for '
                          f'a scientific table (max allowed: {max_rows_and_columns[ax]}).',
                    instructions=instructions
                )

    CHOICE_OF_CHECKS = {
        check_df_is_a_result_of_describe: True,  # We want to start with detecting describe tables.
        check_df_index_is_a_range: True,
        check_df_for_repeated_values: True,
        check_df_for_repeated_values_in_prior_dfs: True,
        check_df_size: True,
    } | DfContentChecker.CHOICE_OF_CHECKS


@dataclass
class FigureDfContentChecker(DfContentChecker):
    func: Callable = df_to_figure
    ALLOW_MULTI_INDEX_FOR_COLUMN_AND_INDEX = {'columns': False, 'index': False}

    DEFAULT_CATEGORY = 'Checking figure'
    P_VALUE_CATEGORY = 'Plotting P-values'

    def check_that_specified_columns_exist(self):
        """
        Check if the columns specified in the `y` and `yerr` arguments exist in the df.
        """
        base_arg_names = ['', 'err', '_ci', '_p_value']
        for xy in ['x', 'y']:
            args = self.get_xy_err_ci_p_value(xy, as_list=True, flatten=True)
            arg_names = [xy + arg_name for arg_name in base_arg_names]
            for arg, arg_name in zip(args, arg_names):
                if arg is None:
                    continue
                un_specified_columns = [col for col in arg if col not in self.df.columns]
                if un_specified_columns:
                    self._append_issue(
                        issue=f'The columns {un_specified_columns} specified in the `{arg_name}` argument do not exist '
                              f'in the df.',
                        instructions=f'Available columns are: {self.df.columns}.',
                    )

    def check_df_size(self):
        """
        Check if the df has too many columns or rows
        """
        shape = self.get_relevant_part_of_df().shape
        max_rows_and_columns = self._get_max_rows_and_columns()
        if is_lower_eq(shape[0], max_rows_and_columns[0]) and is_lower_eq(shape[1], max_rows_and_columns[1]):
            return
        max_rows, max_columns = max_rows_and_columns
        if not is_lower_eq(shape[0], max_rows):
            self._append_issue(
                category=self.SIZE_CATEGORY,
                issue=f'The df of this figure has {shape[0]} rows, which is too many '
                      f'(max allowed: {max_rows}).',
                instructions=dedent_triple_quote_str(f"""
                        Please revise the code so that this figure df shows a maximum of {max_rows} rows.
                        Note that simply trimming the data is typically not a good solution.
                        Carefully consider the data that is most important to show, and remove other rows.
                        Or, consider representing the data more aggregated.
                """)
            )
        num_series = len(self.get_y_labels())
        columns_per_series = shape[1] / num_series
        max_series = int(max_columns / columns_per_series)
        if not is_lower_eq(shape[1], max_columns) and num_series > 2:
            self._append_issue(
                category=self.SIZE_CATEGORY,
                issue=f'This figure has {num_series} series which is too many for a single plot.',
                instructions=f'Please revise the code so that this figure df shows a maximum of {max_series} series.'
            )

    def check_that_y_values_are_numeric(self):
        y, yerr, y_ci, y_p_value = self.get_xy_err_ci_p_value('y', as_list=True)
        for column in y:
            if not pd.api.types.is_numeric_dtype(self.df[column]):
                self._append_issue(
                    issue=f'Column `{column}` is not numeric, so it is not suitable for a plot.',
                    instructions='All columns specified by the `y` argument must have numeric values.',
                )

    def check_that_x_values_are_numeric(self):
        x, xerr, x_ci, x_p_value = self.get_xy_err_ci_p_value('x', as_list=True)
        for column in x:
            if not pd.api.types.is_numeric_dtype(self.df[column]):
                self._append_issue(
                    issue=f'The x-column `{column}` is not numeric.',
                    instructions='If you are attempting to define non-numerical x labels, '
                                 'move the column to the index of the df, and set `x=None` in df_to_figure.\n'
                                 'Otherwise, only use the `x` argument for numeric x values.',
                )

    def _get_columns_containing_p_values(self):
        return [col for col in self.df.columns if is_containing_p_value(self.df[col])]

    def _get_columns_with_p_values_only(self):
        return [col for col in self.df.columns if is_only_p_values(self.df[col])]

    def check_for_mixing_p_values(self):
        # check that the columns with p-values only contain p-values:
        containing_p_values = self._get_columns_containing_p_values()
        not_pure_p_values = [col for col in containing_p_values if col not in self._get_columns_with_p_values_only()]
        if not_pure_p_values:
            self._append_issue(
                category=self.P_VALUE_CATEGORY,
                issue=f'The df has columns {not_pure_p_values}, which contain p-values and non-p-values.',
                instructions='Please make sure that the columns with p-values only contain p-values.',
            )

    def check_that_y_p_value_are_p_values(self):
        p_value_columns = self._get_columns_with_p_values_only()
        y, yerr, y_ci, y_p_value = self.get_xy_err_ci_p_value('y', as_list=True)
        chosen_columns_are_not_p_values = [col for col in y_p_value if col not in p_value_columns]
        if chosen_columns_are_not_p_values:
            self._append_issue(
                category=self.P_VALUE_CATEGORY,
                issue=f'The columns y_p_value={chosen_columns_are_not_p_values} are not p-values.',
                instructions='Please make sure that the columns with p-values only contain p-values.',
            )

    def check_all_p_values_are_in_y_p_value(self):
        p_value_columns = self._get_columns_with_p_values_only()
        y, yerr, y_ci, y_p_value = self.get_xy_err_ci_p_value('y', as_list=True)
        p_value_columns_not_in_y_p_value = [col for col in p_value_columns if col not in y_p_value]
        if p_value_columns_not_in_y_p_value:
            self._append_issue(
                category=self.P_VALUE_CATEGORY,
                issue=f'The columns {p_value_columns_not_in_y_p_value} contain p-values but are not in y_p_value.',
                instructions='Please include all the columns with p-values in y_p_value argument, or remove them '
                             'from the df before plotting.',
                forgive_after=1,
            )

    def check_for_max_number_of_bars(self):
        if self.kind not in ['bar', 'barh']:
            return
        y, yerr, y_ci, y_p_value = self.get_xy_err_ci_p_value('y', as_list=True)
        n_bars = len(self.df) * len(y)
        if not is_lower_eq(n_bars, MAX_BARS):
            self._append_issue(
                issue=f'The plot has {n_bars} bars, which is a large number.',
                instructions='Consider reducing the number of bars to make the plot more readable.',
                forgive_after=2,
            )

    def check_that_y_values_are_diverse(self):
        # There is no point in plotting a box, violin, hist if the y values are not diverse
        if self.kind not in ['box', 'violin', 'hist']:
            return
        y, yerr, y_ci, y_p_value = self.get_xy_err_ci_p_value('y', as_list=True)
        for column in y:
            n_unique = self.df[column].nunique()
            if n_unique <= 2:
                self._append_issue(
                    issue=f'Column `{column}` has only {n_unique} unique values, so it is not suitable for '
                          f'a "{self.kind}" plot.',
                    instructions='Choose another kind of plot, like calculating the mean and plotting a bar plot.',
                )

    def check_for_numeric_x_for_line_and_scatter(self):
        """check that we do not have non-numeric x:"""
        if self.kind not in ['line', 'scatter']:
            return
        if not pd.api.types.is_numeric_dtype(self._get_x_values()):
            self._append_issue(
                issue=f'The x values are not numeric, so they are not suitable for a "{self.kind}" plot.',
                instructions='Consider another kind of plot, like a bar plot (kind="bar").',
            )

    CHOICE_OF_CHECKS = {
        DfContentChecker.check_df_headers_type: True,
        check_that_specified_columns_exist: True,
        DfContentChecker.check_df_for_nan_values: True,
        DfContentChecker.check_df_value_types: True,
        check_for_max_number_of_bars: True,
        check_df_size: True,
        check_that_y_values_are_numeric: True,
        check_that_x_values_are_numeric: True,
        check_for_mixing_p_values: True,
        check_that_y_p_value_are_p_values: True,
        check_all_p_values_are_in_y_p_value: True,  # TODO: maybe disable this check
        check_that_y_values_are_diverse: True,
        check_for_numeric_x_for_line_and_scatter: True,
    }


""" COMPILATION """


@dataclass
class CompilationDfContentChecker(BaseContentDfChecker):
    intermediate_results: Dict[str, Any] = field(default_factory=lambda: {'width': None})
    tolerance_for_too_wide_in_pts: Optional[float] = 25.  # If None, do not raise on too wide.
    DEFAULT_CATEGORY = 'Table/Figure compilation failure'

    def check_creating_latex_and_html(self):
        for is_html in [False, True]:
            with OnStrPValue(OnStr.SMALLER_THAN):
                result, e = self._run_and_get_result_and_exception(is_html=is_html)
            if e is not None:
                self._append_issue(
                    issue=f'Failed to create the table. Got:\n{e}',
                    instructions='Please revise the code to fix the issue.',
                )
                return True

    CHOICE_OF_CHECKS = BaseContentDfChecker.CHOICE_OF_CHECKS | {
        check_creating_latex_and_html: True,
    }


@dataclass
class FigureCompilationDfContentChecker(CompilationDfContentChecker):
    func: Callable = df_to_figure

    def check_compilation_and_create_the_figure(self):
        """
        Axis parameters are returned and stored in intermediate_results.
        """
        if self.output_folder is None:
            return
        filepath = self.output_folder / f'{self.filename}.png'
        axis_parameters, exception = \
            run_create_fig_for_df_to_figure_and_get_axis_parameters(self.df, filepath, **self.kwargs_for_plot)
        if exception is not None:
            self._append_issue(
                issue=f'Failed to create the figure. Got:\n{exception}',
                instructions='Please revise the code to fix the issue.',
            )
            return True
        self.intermediate_results['axis_parameters'] = axis_parameters

    CHOICE_OF_CHECKS = CompilationDfContentChecker.CHOICE_OF_CHECKS | {
        check_compilation_and_create_the_figure: True,
    }


@dataclass
class TableCompilationDfContentChecker(CompilationDfContentChecker):
    func: Callable = df_to_latex

    def _df_to_latex_transpose(self):
        assert 'columns' not in self.kwargs, "assumes columns is None"
        kwargs = self.kwargs.copy()
        index = kwargs.pop('index', True)
        header = kwargs.pop('header', True)
        header, index = index, header
        return df_to_latex(self.df.T, self.filename, index=index, header=header, **kwargs)

    def check_compilation_and_get_width(self):
        exception = None
        with RegisteredRunContext.temporarily_disable_all():
            with OnStrPValue(OnStr.SMALLER_THAN):
                latex = df_to_latex(self.df, self.filename, **self.kwargs)
            try:
                width = self.latex_document.compile_table(latex)
            except BaseLatexProblemInCompilation as e:
                exception = e
                width = None

        # save the width of the table:
        self.intermediate_results['width'] = width

        if exception:
            self._append_issue(
                category='Table pdflatex compilation failure',
                issue=dedent_triple_quote_str("""
                    Here is the created table:

                    ```latex
                    {table}
                    ```

                    When trying to compile it using pdflatex, I got the following error:

                    {error}

                    """).format(filename=self.filename, table=latex, error=exception),
            )
        elif width > 1.3:
            # table is too wide
            # Try to compile the transposed table:
            with OnStrPValue(OnStr.SMALLER_THAN):
                latex_transpose = self._df_to_latex_transpose()
            e_transpose = None
            with RegisteredRunContext.temporarily_disable_all():
                try:
                    width_transpose = self.latex_document.compile_table(latex_transpose)
                except BaseLatexProblemInCompilation as e:
                    e_transpose = e
                    width_transpose = None
            if not e_transpose and width_transpose < 1.1:
                transpose_message = '- Alternatively, consider completely transposing the table. Use `df = df.T`.'
            else:
                transpose_message = ''
            index_note = ''
            column_note = ''
            if self.index:
                longest_index_labels = _find_longest_labels_in_index(self.df.index)
                longest_index_labels = [label for label in longest_index_labels if label is not None and len(label) > 6]
                with OnStrPValue(OnStr.SMALLER_THAN):
                    longest_column_labels = _find_longest_labels_in_columns_relative_to_content(self.df)
                longest_column_labels = [label for label in longest_column_labels if len(label) > 6]
                if longest_index_labels:
                    index_note = dedent_triple_quote_str(f"""\n
                        - Rename any long index labels to shorter names \t
                        (for instance, some long label(s) in the index are: {longest_index_labels}). \t
                        Use `df.rename(index=...)`
                        """)

                if longest_column_labels:
                    column_note = dedent_triple_quote_str(f"""\n
                        - Rename any long column labels to shorter names \t
                        (for instance, some long label(s) in the columns are: {longest_column_labels}). \t
                        Use `df.rename(columns=...)`
                        """)

            if not index_note and not column_note and not transpose_message:
                drop_column_message = dedent_triple_quote_str("""\n
                    - Drop unnecessary columns. \t
                    If the labels cannot be shortened much, consider whether there might be any \t
                    unnecessary columns that we can drop. \t
                    Use `df_to_latex(df, filename, columns=...)`.
                    """)
            else:
                drop_column_message = ''

            self._append_issue(
                category='Table too wide',
                issue=dedent_triple_quote_str("""
                    Here is the created table:

                    ```latex
                    {table}
                    ```
                    I tried to compile it, but the table is too wide. 
                    """).format(filename=self.filename, table=latex),
                instructions="Please change the code to make the table narrower. "
                             "Consider any of the following options:\n"
                             + index_note + column_note + drop_column_message + transpose_message,
            )
        else:
            # table is fine
            pass

    CHOICE_OF_CHECKS = CompilationDfContentChecker.CHOICE_OF_CHECKS | {
        check_compilation_and_get_width: True,
    }


""" CONTENT FOR DISPLAY-ITEM STEP """


@dataclass
class SecondContentChecker(BaseContentDfChecker):

    UNWANTED_LABELS = ['intercept']

    def _is_label_unwanted(self, label):
        if isinstance(label, str):
            return any(label.lower() in unwanted_label for unwanted_label in self.UNWANTED_LABELS)

    def check_for_unwanted_labels_in_x_or_y(self):
        for xy in ['x', 'y']:
            labels = self.get_x_labels() if xy == 'x' else self.get_y_labels()
            unwanted_labels = [label for label in labels if self._is_label_unwanted(label)]
            if unwanted_labels:
                nice_unwanted_labels = NiceList(unwanted_labels, wrap_with='"')
                self._append_issue(
                    category='Atypical choice of data to present',
                    issue=f'The {self.table_or_figure} includes data of {nice_unwanted_labels}.',
                    instructions=dedent_triple_quote_str(f"""
                        Including {nice_unwanted_labels} in a scientific {self.table_or_figure} is not common.
                        Please consider removing the {nice_unwanted_labels}.
                        """),
                    forgive_after=2,
                )

    CHOICE_OF_CHECKS = BaseContentDfChecker.CHOICE_OF_CHECKS | {
        check_for_unwanted_labels_in_x_or_y: True,
    }


@dataclass
class TableSecondContentChecker(SecondContentChecker):
    func: Callable = df_to_latex

    def check_for_repetitive_value_in_column(self):
        for icol in range(self.df.shape[1]):
            column_label = self.df.columns[icol]
            data = self.df.iloc[:, icol]
            if is_containing_p_value(data):
                continue
            try:
                data_unique = data.unique()
            except Exception:  # noqa
                data_unique = None
            if data_unique is not None and len(data_unique) == 1 and len(data) > 5:
                data0 = data.iloc[0]
                # check if the value is a number
                if not isinstance(data0, (int, float, np.number)):
                    pass
                elif round(data0) == data0 and data0 < 10:
                    pass
                else:
                    self._append_issue(
                        category='Same value throughout a column',
                        issue=f'The column "{column_label}" has the same unique value for all rows.',
                        instructions=dedent_triple_quote_str(f"""
                            Please revise the code so that it:
                            * Finds the unique values (use `{column_label}_unique = df["{column_label}"].unique()`)
                            * Asserts that there is only one value. (use `assert len({column_label}_unique) == 1`)
                            * Drops the column from the df (use `df.drop(columns=["{column_label}"])`)
                            * Adds the unique value, {column_label}_unique[0], \t
                            in the {self.table_or_figure} note \t
                            (e.g., `{self.func_name}(..., note=f'For all rows, \t
                            the {column_label} is {{{column_label}_unique[0]}}')`)

                            There is no need to add corresponding comments to the code. 
                            """),
                    )

    CHOICE_OF_CHECKS = SecondContentChecker.CHOICE_OF_CHECKS | {
        check_for_repetitive_value_in_column: True,
    }


@dataclass
class SecondFigureContentChecker(SecondContentChecker):
    func: Callable = df_to_figure

    ODDS_RATIO_TERMS_CAPS = [('odds ratio', False), ('OR', True)]

    @property
    def axis_parameters(self) -> AxisParameters:
        return self.intermediate_results.get('axis_parameters')

    def check_log_scale_for_odds_ratios(self):
        """
        Odds ratios should typically be plotted on a log scale.
        Check if the x or y label contains the term "odds ratio".
        """
        for axis in ['x', 'y']:
            label = self.axis_parameters.xlabel if axis == 'x' else self.axis_parameters.ylabel
            is_log = self.axis_parameters.xscale == 'log' if axis == 'x' else self.axis_parameters.yscale == 'log'
            if label is not None and is_log is not True:
                for term, is_caps in self.ODDS_RATIO_TERMS_CAPS:
                    modified_label = label.lower() if not is_caps else label
                    if term in modified_label:
                        self._append_issue(
                            category='Plotting odds ratios',
                            issue=f'The {axis}-axis label contains the term "{term}". Are you plotting odds ratios?\n'
                                  f'If so, odds ratios are typically shown on a log scale; ',
                            instructions=f'Consider using a log scale for the {axis}-axis (setting `log{axis}=True`).',
                            forgive_after=1,
                        )
                        break

    CHOICE_OF_CHECKS = SecondContentChecker.CHOICE_OF_CHECKS | {
        check_log_scale_for_odds_ratios: True,
    }


""" ANNOTATION """


@dataclass
class AnnotationDfChecker(BaseContentDfChecker):
    stop_after_first_issue: bool = False

    UN_ALLOWED_CHARS = [
        # ('_', 'underscore'),
        ('^', 'caret'),
        ('{', 'curly brace'),
        ('}', 'curly brace')
    ]

    @property
    def width(self):
        return self.intermediate_results.get('width')

    @property
    def is_narrow(self):
        return isinstance(self.width, float) and self.width < 0.8

    def check_for_unallowed_characters_in_labels(self):
        any_issues = False
        for char, char_name in self.UN_ALLOWED_CHARS:
            for is_row in [True, False]:
                if is_row:
                    labels = extract_df_row_labels(self.df, with_title=True, string_only=True)
                    index_or_columns = 'index'
                else:
                    labels = extract_df_column_labels(self.df, with_title=True, string_only=True)
                    index_or_columns = 'columns'
                unallowed_labels = sorted([label for label in labels if char in label])
                if unallowed_labels:
                    any_issues = True
                    self._append_issue(
                        category=f'The df row/column labels contain un-allowed characters',
                        issue=dedent_triple_quote_str(f"""
                            The "{self.filename}" has {index_or_columns} labels containing \t
                            the character "{char}" ({char_name}), which is not allowed.
                            Here are the problematic {index_or_columns} labels:
                            {unallowed_labels}
                            """),
                        instructions=dedent_triple_quote_str(f"""
                            Please revise the code to map these {index_or_columns} labels to new names \t
                            that do not contain the "{char}" characters. Spaces are allowed.

                            Doublecheck to make sure your code uses `df.rename({index_or_columns}=...)` \t
                            with the `{index_or_columns}` argument set to a dictionary mapping the old \t
                            {index_or_columns} names to the new ones.
                            """)
                    )
        return any_issues  # we don't want additional issues if working on the underscores

    def check_glossary(self):
        axes_labels = extract_df_axes_labels(self.df, with_title=False, string_only=True)
        abbr_labels = [label for label in axes_labels if is_unknown_abbreviation(label)]
        glossary = self.glossary or {}
        un_mentioned_abbr_labels = sorted([label for label in abbr_labels if label not in glossary])
        glossary_keys_not_in_df = sorted([label for label in glossary if label not in axes_labels])

        if un_mentioned_abbr_labels or glossary_keys_not_in_df:
            glossary_msg = f"The `glossary` argument of `{self.func_name}` for '{self.filename}' "
            if self.glossary:
                glossary_msg += f"includes the following keys:\n{list(self.glossary.keys())}\n\n"
            else:
                glossary_msg += "is not provided.\n\n"
            axes_labels_msg = f'The corresponding df includes the following labels:\n{axes_labels}\n\n'
            if glossary_keys_not_in_df:
                glossary_keys_not_in_df_msg = dedent_triple_quote_str(f"""
                    **Provided glossary keys not matching any of the df labels:**
                    The glossary includes the following keys that are not in the df:
                    {glossary_keys_not_in_df}
                    The glossary keys should be a subset of the df labels.
                    Please remove/replace these stranded keys. \t
                    (or, alternatively, rename the relevant df labels to match these stranded glossary keys).
                    """)
            else:
                glossary_keys_not_in_df_msg = ""

            if un_mentioned_abbr_labels:
                un_mentioned_abbr_labels_msg = dedent_triple_quote_str(f"""\n
                    **Abbreviated df labels that are not mentioned in the glossary:**
                    The df includes the following abbreviated labels that are not defined in the glossary:
                    {un_mentioned_abbr_labels}
                    Please add these missing abbreviated labels to the `glossary`.
                    """)
                if self.is_narrow:
                    un_mentioned_abbr_labels_msg += dedent_triple_quote_str(f"""
                        Alternatively, since the {self.table_or_figure} is not too wide, you can also replace \t
                        these undefined abbreviated labels with their full names in the dataframe itself.
                        """)
            else:
                un_mentioned_abbr_labels_msg = ""

            self._append_issue(
                category='Displayitem glossary',
                issue=f'{glossary_msg}{axes_labels_msg}{glossary_keys_not_in_df_msg}{un_mentioned_abbr_labels_msg}',
                instructions=dedent_triple_quote_str(f"""\n
                    As a reminder: you can also use the `note` argument to add \t
                    information that is related to the f"{self.table_or_figure} as a whole, \t
                    rather than to a specific label.
                    """)
            )

    def _create_displayitem_caption_label_issue(self, issue: str):
        self._append_issue(
            category='Problem with displayitem caption',
            issue=issue,
            instructions=dedent_triple_quote_str("""
                Please revise the code making sure all displayitems are created with a caption.
                Use the arguments `caption` of `df_to_latex` or `df_to_figure`.
                Captions should be suitable for tables/figures of a scientific paper.
                In addition, you can add:
                - an optional note for further explanations (use the argument `note`)
                - a glossary mapping any abbreviated row/column labels to their definitions \t
                (use the argument `glossary` argument). 
                """)
        )

    def _check_caption_or_note(self, text: Optional[str], item_name: str = 'caption', is_required: bool = True):
        forbidden_starts: Tuple[str, ...] = ('Figure', 'Table')
        if text is None:
            if is_required:
                self._create_displayitem_caption_label_issue(
                    f'The {self.table_or_figure} does not have a {item_name}.')
            else:
                return
        else:
            for forbidden_start in forbidden_starts:
                if text.startswith(forbidden_start):
                    self._create_displayitem_caption_label_issue(
                        f'The {item_name} of the {self.table_or_figure} should not start with "{forbidden_start}".')
            if '...' in text:
                self._create_displayitem_caption_label_issue(
                    f'The {item_name} of the {self.table_or_figure} should not contain "..."')
            if re.search(pattern=r'<.*\>', string=text):
                self._create_displayitem_caption_label_issue(
                    f'The {item_name} of the {self.table_or_figure} should not contain "<...>"')

    def check_note(self):
        self._check_caption_or_note(self.note, item_name='note', is_required=False)

    def check_caption(self):
        self._check_caption_or_note(self.caption, item_name='caption', is_required=True)

    def check_note_is_different_than_caption(self):
        note, caption = self.note, self.caption
        if note is not None and caption is not None and (
                note.lower() in caption.lower() or caption.lower() in note.lower()):
            self._create_displayitem_caption_label_issue(
                f'The note of the {self.table_or_figure} should not be the same as the caption.\n'
                'Notes are meant to provide additional information, not to repeat the caption.')

    CHOICE_OF_CHECKS = BaseContentDfChecker.CHOICE_OF_CHECKS | {
        check_for_unallowed_characters_in_labels: True,
        check_glossary: True,
        check_note: True,
        check_caption: True,
        check_note_is_different_than_caption: True,
    }


class FigureAnnotationDfChecker(AnnotationDfChecker):
    func: Callable = df_to_figure

    @property
    def axis_parameters(self) -> AxisParameters:
        return self.intermediate_results.get('axis_parameters')

    def check_if_numeric_axes_have_labels(self):
        """
        Check if all axes with numeric labels have labels.
        Return an error message if not.
        """
        axis_parameters = self.axis_parameters
        x_numeric = axis_parameters.is_x_axis_numeric()
        y_numeric = axis_parameters.is_y_axis_numeric()
        msgs = []
        if x_numeric and not axis_parameters.xlabel:
            msgs.append('The x-axis is numeric, but it does not have a label. Use `xlabel=` to add a label.')
        if y_numeric and not axis_parameters.ylabel:
            msgs.append('The y-axis is numeric, but it does not have a label. Use `ylabel=` to add a label.')
        if msgs:
            msg = 'All axes with numeric labels must have labels.\n' + '\n'.join(msgs)
            self._append_issue(
                issue=msg,
                instructions=dedent_triple_quote_str("""
                    Please revise the code to add labels.
                    Use the arguments `xlabel` and `ylabel` of `df_to_figure`.
                    """),
            )

    CHOICE_OF_CHECKS = AnnotationDfChecker.CHOICE_OF_CHECKS | {
        check_if_numeric_axes_have_labels: True,
    }


""" FILE CONTINUITY """


@dataclass
class ContinuityDfChecker(BaseContentDfChecker):
    DEFAULT_CATEGORY = 'File continuity'

    def check_for_file_continuity(self):
        prior_filename = self.df.get_prior_filename()
        if prior_filename is None:
            self._append_issue(
                issue="The df should be created from a previous df (not from scratch).\n"
                      "Only use inplace operations on the df loaded from the previous step.",
            )
            return
        should_be_filename = prior_filename + '_formatted'
        if self.filename != should_be_filename:
            self._append_issue(
                issue=dedent_triple_quote_str(f"""
                    The file name of the loaded df was "{prior_filename}".
                    The current file name should be "{should_be_filename}" (instead of "{self.filename}").
                    """),
            )

    CHOICE_OF_CHECKS = BaseContentDfChecker.CHOICE_OF_CHECKS | {
        check_for_file_continuity: True,
    }


""" RUN CHECKERS """


def create_and_run_chain_checker_from_list_info_df(checkers: List[Type[BaseContentDfChecker]],
                                                   df: InfoDataFrameWithSaveObjFuncCall, **k
                                                   ) -> Tuple[RunIssues, Dict[str, Any]]:
    func_call = df.get_func_call()
    func, args, kwargs = func_call
    filename = func_call.filename
    return create_and_run_chain_checker(checkers, df=df, func=func, filename=filename, kwargs=kwargs, **k)


def check_df_to_figure_analysis(df: InfoDataFrameWithSaveObjFuncCall, **k) -> RunIssues:
    checkers = [
        FigureSyntaxDfChecker,
        FigureDfContentChecker,
        FigureCompilationDfContentChecker,  # This will actually create the png file
    ]
    return create_and_run_chain_checker_from_list_info_df(checkers, df=df, **k)[0]


def check_df_to_latex_analysis(df: InfoDataFrameWithSaveObjFuncCall, **k) -> RunIssues:
    checkers = [
        TableSyntaxDfChecker,
        TableDfContentChecker,
    ]
    return create_and_run_chain_checker_from_list_info_df(checkers, df=df, **k)[0]


def check_df_to_figure_displayitems(df: InfoDataFrameWithSaveObjFuncCall, **k) -> RunIssues:
    checkers = [
        FigureSyntaxDfChecker,
        FigureDfContentChecker,
        FigureCompilationDfContentChecker,  # Create png. Stores annotation messages in intermediate_results
        ContinuityDfChecker,
        SecondFigureContentChecker,
        FigureAnnotationDfChecker,
    ]
    return create_and_run_chain_checker_from_list_info_df(checkers, df=df, **k)[0]


def check_df_to_latex_displayitems(df: InfoDataFrameWithSaveObjFuncCall, **k) -> RunIssues:
    checkers = [
        TableSyntaxDfChecker,
        TableDfContentChecker,
        ContinuityDfChecker,
        TableSecondContentChecker,
        TableCompilationDfContentChecker,
        AnnotationDfChecker,
    ]
    return create_and_run_chain_checker_from_list_info_df(checkers, df=df, **k)[0]


def check_analysis_df(df: InfoDataFrameWithSaveObjFuncCall, **k) -> RunIssues:
    func, args, kwargs = df.get_func_call()
    if func == df_to_figure:
        return check_df_to_figure_analysis(df, **k)
    elif func == df_to_latex:
        return check_df_to_latex_analysis(df, **k)
    else:
        raise ValueError(f"func should be either df_to_figure or df_to_latex, not {func}")


def check_displayitem_df(df: InfoDataFrameWithSaveObjFuncCall, **k) -> RunIssues:
    func = df.get_func_call().func
    if func == df_to_figure:
        return check_df_to_figure_displayitems(df, **k)
    elif func == df_to_latex:
        return check_df_to_latex_displayitems(df, **k)
    else:
        raise ValueError(f"func should be either df_to_figure or df_to_latex, not {func}")


""" FILENAME CHECKERS """


def get_issue_if_filename_not_legit_df_tag(filename: str, func: Callable = None) -> Optional[RunIssue]:
    """
    check if the filename is in the correct format
    """
    checker = SyntaxDfChecker(filename=filename, func=func)
    checker.check_filename()
    return checker.issues[0] if checker.issues else None


def raise_issue_if_filename_not_legit_df_tag(filename: str, func: Callable = None):
    if not isinstance(filename, str):
        raise ValueError(f"filename should be a string, not {type(filename)}")
    issue = get_issue_if_filename_not_legit_df_tag(filename, func)
    if issue:
        raise issue
