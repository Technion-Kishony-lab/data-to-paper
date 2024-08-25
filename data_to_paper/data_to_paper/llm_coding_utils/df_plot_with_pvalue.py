from typing import Optional, Union, Tuple, Iterable

import matplotlib as mpl
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from pandas import DataFrame

from data_to_paper.run_gpt_code.overrides.pvalue import PValueToStars, OnStr, OnStrPValue
from .describe import describe_value, df_to_numerically_labeled_latex, describe_df
from .matplotlib_utils import get_xy_coordinates_of_df_plot, \
    replace_singleton_legend_with_axis_label, add_grid_line_at_zero_if_not_origin, rotate_xticklabels_if_not_numeric
from ..run_gpt_code.overrides.dataframes.utils import to_html_with_value_format
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
ColumnChoice = Union[str, NoneType, Iterable[str]]


def _get_errors(df: pd.DataFrame, columns: ColumnChoice, arg_name: str, scalars_only: bool = None):
    """
    We allow referring to columns as strings or iterables of strings.
    Each such column is expected to contain either scalar values or tuples of two scalar values.

    scalars_only:
        True:  only columns with scalar values are allowed. Return array (n, 2, m)
        False: only tuples of two scalar values are allowed. Return array (n, 1, m)
        None:  both are allowed. scalar columns are converted to tuples of two identical values.
                  Return array of shape (n, 2, m).

    """
    if columns is None:
        return None
    if isinstance(columns, str):
        columns = [columns]
    results = []
    for column in columns:
        result = np.array(df[column].to_list())
        if result.ndim == 1:
            if scalars_only is False:
                raise ValueError(f'Argument `{arg_name}` refer to columns with tuples of two values.\n'
                                 f'But, column `{column}` contains only scalar values.')
            if scalars_only is None:
                result = np.array([result, result])
            else:
                result = np.array([result])
        else:
            if scalars_only is True:
                raise ValueError(f'Argument `{arg_name}` refer to columns with scalar values.\n'
                                 f'But, column `{column}` contains multi-dimensional values.')
            result = result.T
        results.append(result)
    results = np.array(results)
    return results


def _convert_err_and_ci_to_err(df: pd.DataFrame, xy: Optional[str],
                               xy_name: str,
                               err: Optional[str], ci: Optional[Union[str, Tuple[str, str]]]
                               ) -> Optional[np.ndarray]:
    """
    Create a confidence interval from a dataframe.
    """
    err_name = f'{xy_name}err'
    ci_name = f'{xy_name}_ci'
    if err is not None:
        if ci is not None:
            raise ValueError(f'The `{err_name}` and `{ci_name}` arguments cannot be used together.')
        return _get_errors(df, err, err_name, scalars_only=None)
    if ci is None:
        return None
    ci_vals = _get_errors(df, ci, ci_name, scalars_only=False)
    nominal = df[xy].to_numpy().T  # (n, m)
    return np.array([nominal - ci_vals[:, 0, :], ci_vals[:, 1, :] - nominal]).swapaxes(0, 1)


def _check_matching_column_choice(primary_name, optional_name, primary, optional):
    if primary is None:
        if optional is None:
            return
        raise ValueError(f'The `{optional_name}` argument cannot be provided without the `{primary_name}` argument.')
    elif optional is None:
        pass
    elif isinstance(primary, str):
        if not isinstance(optional, str):
            raise ValueError(f'If `{primary_name}` is a string, `{optional_name}` must be a string.')
    elif isinstance(primary, Iterable):
        if not isinstance(optional, Iterable):
            raise ValueError(f'If `{primary_name}` is an iterable, `{optional_name}` must be an iterable.')
        if len(primary) != len(optional):
            raise ValueError(f'If `{primary_name}` is an iterable, `{optional_name}` must have the same length.')
    else:
        raise ValueError(f'`{primary_name}` should be a string or an iterable of strings.')


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
                        xerr: Optional[str] = None, yerr: ColumnChoice = None,
                        y_ci: ColumnChoice = None,
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
            msg = f'Error calling df.plot(x={describe_value(x)}, y={describe_value(y)}, kind={kind}, xerr={describe_value(xerr)}, yerr={describe_value(yerr)}, **{kwargs}):\n' \
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
            y_p_values = _get_errors(df, y_p_value, 'y_p_value', scalars_only=True)
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
    len_df = len(df)
    too_long = len_df > 25
    if too_long:
        df = df.head(3)
    if is_html:
        df_str = to_html_with_value_format(df, border=0, justify='left')
    else:
        with OnStrPValue(OnStr.SMALLER_THAN):
            df_str = describe_df(df, should_format=should_format)
    if too_long:
        df_str += (f'\n...\n'
                   f'Total number of rows: {len_df}\n')

    kwargs = kwargs.copy()
    ci_x = kwargs.pop('x_ci', None)
    ci_y = kwargs.pop('y_ci', None)
    p_value_x = kwargs.pop('x_p_value', None)
    p_value_y = kwargs.pop('y_p_value', None)

    h = f'This latex figure presents "{fig_filename}" which was created from the following df:\n\n'

    s = '\n\n'
    s += f'To create the figure, this df was plotted with the following command:\n\n'
    s += f'df.plot(**{kwargs})'
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
             f'(with thresholds indicated in the figure caption).'
    if is_html:
        h = text_to_html(h)
        s = text_to_html(s)
    return h + df_str + s
