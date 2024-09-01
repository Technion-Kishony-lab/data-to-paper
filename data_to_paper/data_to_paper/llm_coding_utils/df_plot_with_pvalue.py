from typing import Optional, Union, Tuple, Iterable, List

import matplotlib as mpl
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from pandas import DataFrame

from data_to_paper.run_gpt_code.overrides.pvalue import PValueToStars, OnStr, OnStrPValue
from .describe import describe_value, describe_df
from .matplotlib_utils import get_xy_coordinates_of_df_plot, \
    replace_singleton_legend_with_axis_label, add_grid_line_at_zero_if_not_origin, rotate_xticklabels_if_not_numeric
from ..research_types.hypothesis_testing.env import MAX_BARS
from ..run_gpt_code.overrides.dataframes.utils import df_to_html_with_value_format
from ..utils import dedent_triple_quote_str
from ..utils.check_type import raise_on_wrong_func_argument_types_decorator
from ..utils.highlighted_text import text_to_html

RC_PARAMS = {
    'figure.figsize': [10, 6],
    'font.size': 14,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.facecolor': 'white',
    'axes.facecolor': 'white'
}

NoneType = type(None)
ColumnChoice = Union[str, NoneType, List[str]]
ColumnChoiceWithPairs = Union[str, NoneType, List[str], Tuple[str, str], List[Tuple[str, str]]]


example_plotting = dedent_triple_quote_str("""
    Example of proper use of the `df_to_figure`:
    
    df = pd.DataFrame({
        'apple': [1, 2, 3],
        'banana': [4, 5, 6],
        'apple_ci': [(0.9, 1.1), (1.8, 2.2), (2.7, 3.3)],
        'banana_ci_low': [3.9, 4.8, 5.7],
        'banana_ci_high': [4.1, 5.2, 6.3],
        'apple_p_value': [0.1, 0.05, 0.001],
        'banana_p_value': [0.1, 0.05, 0.001],
    })
    
    # Example 1: ci stored as tuples in a single column
    df_to_figure(df, 'example', y='apple', y_ci='apple_ci', y_p_value='apple_p_value')
    
    # Example 2: ci stored as two separate columns
    df_to_figure(df, 'example', y='banana', y_ci=('banana_ci_low', 'banana_ci_high'), y_p_value='banana_p_value')
    
    # Example 3: multiple y columns
    df_to_figure(df, 'example', 
        y=['apple', 'banana'],
        y_ci=['apple_ci', ('banana_ci_low', 'banana_ci_high')],
        y_p_value=['apple_p_value', 'banana_p_value'])
    """)


def _get_errors(df: pd.DataFrame, columns: ColumnChoiceWithPairs, arg_name: str, scalars_only: bool = None,
                is_list: bool = False, xy_name: str = 'y') -> Optional[np.ndarray]:
    """
    We allow referring to columns as strings or iterables of strings, or tuples of two strings, or iterables of tuples.
    Each such column is expected to contain either scalar values or tuples of two scalar values.

    scalars_only:
        True:  only columns with scalar values are allowed. Return array (n, 1, m)
        False: only tuples of two scalar values are allowed. Return array (n, 2, m)
        None:  both are allowed. scalar columns are converted to tuples of two identical values.
                  Return array of shape (n, 2, m).

    is_list:
        Designates whether the primary (namely the corresponding 'x', or 'y') argument is a list.
    """
    if columns is None:
        return None
    if isinstance(columns, (str, Tuple)):
        columns = [columns]
    results = []
    for column in columns:
        err = None
        if isinstance(column, Tuple):
            column = list(column)
        result = np.array(np.array(df[column]).tolist()).reshape(len(df), -1)
        if result.shape[1] == 1:
            assert isinstance(column, str)

            if scalars_only is False:
                err = dedent_triple_quote_str(f"""
                    either:
                        - a single string referring to a single column with two-value tuples of the ci (low, high)
                        - a tuple of two strings referring to two columns with scalar values (the low and high ci)
                    But column `{column}` contains scalar values.
                    """)
            if scalars_only is None:
                result = np.concatenate([result, result], axis=1)
        else:
            if scalars_only is True:
                err = dedent_triple_quote_str(f"""
                    a string referring to a column with scalar values.
                    But column `{column}` contains multi-dimensional values.
                    """)
        if err:
            if is_list:
                pre_msg = f"When the `{xy_name}` argument is a list of columns, " \
                          f"`{arg_name}` should be a list of matching length, with each element being "
            else:
                pre_msg = f"When the `{xy_name}` argument is a single string (referring to a column), " \
                          f"`{arg_name}` should be "
            raise ValueError(pre_msg + err + '\n\n' + example_plotting)

        results.append(result.T)
    results = np.array(results)
    return results


def _convert_err_and_ci_to_err(df: pd.DataFrame, xy: ColumnChoice, xy_name: str,
                               err: ColumnChoiceWithPairs, ci: ColumnChoiceWithPairs) -> Optional[np.ndarray]:
    """
    Create a confidence interval from a dataframe.
    """
    err_name = f'{xy_name}err'
    ci_name = f'{xy_name}_ci'
    if ci is None and err is None:
        return None
    if err is not None and ci is not None:
        raise ValueError(f'Error bars should be specified with either `{err_name}` or `{ci_name}` arguments, '
                         f'not both.\n\n{example_plotting}')
    if err is not None:
        return _get_errors(df, err, err_name, scalars_only=None, is_list=isinstance(xy, List), xy_name=xy_name)
    ci_vals = _get_errors(df, ci, ci_name, scalars_only=False, is_list=isinstance(xy, List), xy_name=xy_name)
    nominal = df[xy].to_numpy().T  # (n, m)
    return np.array([nominal - ci_vals[:, 0, :], ci_vals[:, 1, :] - nominal]).swapaxes(0, 1)


def _check_matching_column_choice(primary_name, optional_name, primary: ColumnChoice, optional: ColumnChoiceWithPairs):
    if primary is None:
        if optional is None:
            return
        raise ValueError(f'The `{optional_name}` argument cannot be provided without the `{primary_name}` argument.'
                         f'\n\n{example_plotting}')
    elif optional is None:
        pass
    elif isinstance(primary, str):
        if not isinstance(optional, (str, tuple)):
            raise ValueError(f'If `{primary_name}` is str, `{optional_name}` must be a str, or Tuple[str, str].'
                             f'\n\n{example_plotting}')
    elif isinstance(primary, List):
        if not isinstance(optional, List) or len(primary) != len(optional):
            raise ValueError(f'If `{primary_name}` is a list, `{optional_name}` must be a list with the same length.'
                             f'\n\n{example_plotting}')
    else:
        raise ValueError(f'`{primary_name}` should be a string or an list of strings.'
                         f'\n\n{example_plotting}')


def df_plot_with_legend(df: DataFrame, x: Optional[str] = None, y: ColumnChoice = None,
                        **kwargs):
    """
    Same as df.plot, but replaces underscores in the df columns with spaces to allow for better legend display.
    df.plot will otherwise skip columns with underscores in the legend.
    """

    def replace_underscores_with_spaces(s):
        if not isinstance(s, str):
            return s
        return s.replace('_', ' ')

    # find all the underscores in the column names:
    df = df.copy()
    columns = df.columns
    columns_with_spaces = [replace_underscores_with_spaces(col) for col in columns]
    df.columns = columns_with_spaces
    rows = df.index
    rows_with_spaces = [replace_underscores_with_spaces(row) for row in rows]
    df.index = rows_with_spaces

    # replace in `y`:
    if isinstance(y, str):
        y = y.replace('_', ' ')
    elif isinstance(y, Iterable):
        y = [col.replace('_', ' ') for col in y]

    if isinstance(x, str):
        x = x.replace('_', ' ')

    return df.plot(x=x, y=y, **kwargs)


@raise_on_wrong_func_argument_types_decorator
def df_plot_with_pvalue(df: DataFrame, x: Optional[str] = None, y: ColumnChoice = None,
                        kind: str = 'line', ax: Optional[plt.Axes] = None,
                        xerr: Optional[str] = None, yerr: ColumnChoiceWithPairs = None,
                        y_ci: ColumnChoiceWithPairs = None,
                        y_p_value: ColumnChoice = None,
                        **kwargs):
    """
    Same as df.plot, but allows for plotting p-values as 'NS', '*', '**', or '***'.
    p_value: A string representing the column name of the p-values.
    """
    if y is None:
        raise ValueError('The `y` argument must be provided, indicating the column(s) to plot.')
    _check_matching_column_choice('y', 'y_p_value', y, y_p_value)
    _check_matching_column_choice('y', 'yerr', y, yerr)
    _check_matching_column_choice('y', 'y_ci', y, y_ci)
    xerr = _convert_err_and_ci_to_err(df, x, 'x', xerr, None)
    yerr = _convert_err_and_ci_to_err(df, y, 'y', yerr, y_ci)
    with mpl.rc_context(rc=RC_PARAMS):
        try:
            ax = df_plot_with_legend(df, x=x, y=y, kind=kind, ax=ax, xerr=xerr, yerr=yerr, **kwargs)
        except Exception as e:
            msg = f'Error calling df.plot(x={describe_value(x)}, y={describe_value(y)}, kind={kind}, ' \
                  f'xerr={describe_value(xerr)}, yerr={describe_value(yerr)}, **{kwargs}):\n' \
                  f'Got the following exception:\n{e}'
            raise ValueError(msg)
        coords = get_xy_coordinates_of_df_plot(df, x=x, y=y, kind=kind)
        replace_singleton_legend_with_axis_label(ax, kind)
        rotate_xticklabels_if_not_numeric(ax)
        if kind == 'bar':
            add_grid_line_at_zero_if_not_origin(ax, 'h')
        if kind == 'barh':
            add_grid_line_at_zero_if_not_origin(ax, 'v')

        if y_p_value:
            y_p_values = _get_errors(df, y_p_value, 'y_p_value', scalars_only=True,
                                     is_list=isinstance(y, List), xy_name='y')
            if yerr is None:
                raise ValueError('The `yerr` or `y_ci` argument must be provided when including `y_p_value`.')
            for col_index, index_data in coords.items():
                for row_index, (x, y) in index_data.items():
                    p_val = y_p_values[col_index, 0, row_index]
                    errs = yerr[col_index, :, row_index]
                    if kind == 'bar' and y < 0:
                        y_plt = y - errs[0]
                        va = 'top'
                    else:
                        y_plt = y + errs[1]
                        va = 'baseline'
                    ax.text(x, y_plt, PValueToStars(p_val).convert_to_stars(), ha='center', va=va)
    return ax


def get_description_of_plot_creation(df, fig_filename, kwargs, is_html: bool = True,
                                     should_format: bool = False
                                     ) -> str:
    """
    Get a description of how the plot was created.
    This is what the LLM will get. This is essentially how the LLM "sees" the figure.
    More sophisticated implementations can be added in the future.
    """
    if is_html:
        len_df = len(df)
        too_long = len_df > MAX_BARS
        if too_long:
            df = df.head(3)
        df_str = df_to_html_with_value_format(df, border=0, justify='left')
        if too_long:
            df_str += f'<br>... total {len_df} rows\n'
    else:
        with OnStrPValue(OnStr.SMALLER_THAN):
            df_str = describe_df(df, should_format=should_format, max_rows=MAX_BARS)

    kwargs = kwargs.copy()
    ci_x = kwargs.pop('x_ci', None)
    ci_y = kwargs.pop('y_ci', None)
    p_value_x = kwargs.pop('x_p_value', None)
    p_value_y = kwargs.pop('y_p_value', None)

    h = f'This latex figure presents "{fig_filename}",\nwhich was created from the df:\n\n'

    s = '\n\n'
    s += f'To create the figure, this df was plotted with the command:\n\n'
    s += f'df.plot({", ".join([f"{k}={repr(v)}" for k, v in kwargs.items()])})'
    if ci_x:
        s += f'\n\nConfidence intervals for x-values were then plotted based on column: {repr(ci_x)}.'
    if ci_y:
        s += f'\n\nConfidence intervals for y-values were then plotted based on column: {repr(ci_y)}.'
    if p_value_x:
        s += f'\n\nP-values for x-values were taken from column: {repr(p_value_x)}.'
    if p_value_y:
        s += f'\n\nP-values for y-values were taken from column: {repr(p_value_y)}.'
    if p_value_x or p_value_y:
        s += f'\n\nThese p-values were presented above the data points as stars ' \
             f'(with significance threshold values indicated in the figure caption).'
    if is_html:
        h = text_to_html(h)
        s = text_to_html(s)
    return h + df_str + s
