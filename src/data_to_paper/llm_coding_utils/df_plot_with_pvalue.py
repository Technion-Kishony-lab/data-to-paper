from typing import Optional, Union, Tuple, List

import matplotlib as mpl
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from pandas import DataFrame

from data_to_paper.text import dedent_triple_quote_str
from data_to_paper.utils.check_type import raise_on_wrong_func_argument_types_decorator
from data_to_paper.text.highlighted_text import text_to_html
from data_to_paper.utils.numerics import is_lower_eq

from data_to_paper.run_gpt_code.overrides.pvalue import PValueToStars, OnStr, OnStrPValue
from .consts import DfColumnTyping
from .describe import describe_value, describe_df
from .matplotlib_utils import get_xy_coordinates_of_df_plot, \
    replace_singleton_legend_with_axis_label, add_grid_line_at_base_if_needed, rotate_xticklabels_if_not_numeric
from ..run_gpt_code.overrides.dataframes.utils import df_to_html_with_value_format

RC_PARAMS = {
    'savefig.facecolor': 'white',
    'axes.facecolor': 'white'
}

NoneType = type(None)
ColumnChoice = Union[DfColumnTyping, NoneType, List[DfColumnTyping]]
ColumnChoiceWithPairs = \
    Union[DfColumnTyping, NoneType, List[DfColumnTyping],
          Tuple[DfColumnTyping, DfColumnTyping], List[Tuple[DfColumnTyping, DfColumnTyping]]]


example_plotting = dedent_triple_quote_str("""
    Example of proper use of the `df_to_figure`:

    # Example 1: ci as (low, high) tuples
    df = pd.DataFrame({
        'apple': [1, 2, 3],
        'banana': [4, 5, 6],
        'apple_ci': [(0.9, 1.1), (1.8, 2.2), (2.7, 3.3)],
        'banana_ci': [(3.9, 4.1), (4.8, 5.2), (5.7, 6.3)],
        'apple_p_value': [0.1, 0.05, 0.001],
        'banana_p_value': [0.1, 0.05, 0.001],
    })

    df_to_figure(df, 'example1', kind='bar', y=['apple', 'banana'], 
        y_ci=['apple_ci', 'banana_ci'],
        y_p_value=['apple_p_value', 'banana_p_value']
    )

    # Example 2: ci as two separate columns
    df = pd.DataFrame({
        'apple': [1, 2, 3],
        'banana': [4, 5, 6],
        'apple_low': [0.9, 1.8, 2.7],
        'apple_high': [1.1, 2.2, 3.3],
        'banana_low': [3.9, 4.8, 5.7],
        'banana_high': [4.1, 5.2, 6.3],
        'apple_p_value': [0.1, 0.05, 0.001],
        'banana_p_value': [0.1, 0.05, 0.001],
    })

    df_to_figure(df, 'example2', kind='bar', y=['apple', 'banana'], 
        y_ci=[('apple_low', 'apple_high'), ('banana_low', 'banana_high')], 
        y_p_value=['apple_p_value', 'banana_p_value']
    )

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
                        - a single string referring to a single column containing two-value tuples (ci_low, ci_high)
                        - a tuple of two strings referring to two columns containing scalar values for \t
                    the low and high values.
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
    errs = np.array([nominal - ci_vals[:, 0, :], ci_vals[:, 1, :] - nominal]).swapaxes(0, 1)
    if np.any(errs < 0):
        raise ValueError(f'Confidence intervals for {xy_name} values must be provided in the form of '
                         f'(low, high) tuples. These values must FLANK the nominal value, '
                         f'but the provided values do not.\n\n{example_plotting}')
    return errs


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


def _get_custom_colors(num_colors: int):
    if num_colors < 2:
        return ["#555599"]
    elif num_colors < 9:
        return ["#555599", '#55aa55', '#994444', "#aaaa22", "#55aaaa", '#994499', "#5599ee", "#ee9955", "#99ee55"]
    return [color['color'] for color in plt.rcParams['axes.prop_cycle']]


@raise_on_wrong_func_argument_types_decorator
def df_plot_with_pvalue(df: DataFrame, x: Optional[DfColumnTyping] = None, y: ColumnChoice = None,
                        kind: str = 'bar', ax: Optional[plt.Axes] = None,
                        xerr: Optional[DfColumnTyping] = None, yerr: ColumnChoiceWithPairs = None,
                        y_ci: ColumnChoiceWithPairs = None,
                        y_p_value: ColumnChoice = None,
                        **kwargs):
    """
    Same as df.plot, but allows for plotting p-values as 'ns', '*', '**', or '***'.
    p_value: A string representing the column name of the p-values.
    """
    if y is None:
        raise ValueError('The `y` argument must be provided, indicating the column(s) to plot.')

    _check_matching_column_choice('y', 'y_p_value', y, y_p_value)
    _check_matching_column_choice('y', 'yerr', y, yerr)
    _check_matching_column_choice('y', 'y_ci', y, y_ci)
    xerr = _convert_err_and_ci_to_err(df, x, 'x', xerr, None)
    yerr = _convert_err_and_ci_to_err(df, y, 'y', yerr, y_ci)

    kwargs = kwargs.copy()
    num_y_cols = len(y) if isinstance(y, list) else 1
    kwargs['color'] = kwargs.get('color', _get_custom_colors(num_y_cols))
    kwargs['edgecolor'] = kwargs.get('edgecolor', 'black')
    kwargs['linewidth'] = kwargs.get('linewidth', 1)
    kwargs['fontsize'] = kwargs.get('fontsize', 9)
    with mpl.rc_context(rc=RC_PARAMS):
        try:
            ax = df.plot(x=x, y=y, kind=kind, ax=ax, xerr=xerr, yerr=yerr, **kwargs)
        except Exception as e:
            msg = f'Error calling df.plot(x={describe_value(x)}, y={describe_value(y)}, kind={describe_value(kind)}, ' \
                  f'xerr={describe_value(xerr)}, yerr={describe_value(yerr)}, **{describe_value(kwargs)}):\n' \
                  f'Got the following exception:\n{e}'
            raise ValueError(msg)
        coords = get_xy_coordinates_of_df_plot(df, x=x, y=y, kind=kind)
        replace_singleton_legend_with_axis_label(ax, kind)

        if y_p_value:
            y_p_values = _get_errors(df, y_p_value, 'y_p_value', scalars_only=True,
                                     is_list=isinstance(y, List), xy_name='y')
            if yerr is None:
                raise ValueError('The `y_ci` argument must be provided when including `y_p_value`.')
            min_y, max_y = ax.get_ylim()
            for col_index, index_data in coords.items():
                for row_index, (x, y) in index_data.items():
                    p_val = y_p_values[col_index, 0, row_index]
                    if not isinstance(p_val, float):
                        raise ValueError(f'P-values must be numeric, but found `{type(p_val)}`.')
                    if p_val < 0 or p_val > 1:
                        raise ValueError(f'P-values must be between 0 and 1, but found `{p_val}`.')
                    errs = yerr[col_index, :, row_index]
                    if kind == 'bar' and y < 0:
                        y_plt = y - errs[0] - (max_y - min_y) * 0.01
                        va = 'top'
                    else:
                        y_plt = y + errs[1] + (max_y - min_y) * 0.01
                        va = 'baseline'
                    text = ax.text(x, y_plt, PValueToStars(p_val).convert_to_stars(), ha='center', va=va, fontsize=7)
                    bbox = text.get_window_extent()
                    inv = ax.transData.inverted()
                    bbox_data = inv.transform_bbox(bbox)
                    text_height = bbox_data.intervaly[1] - bbox_data.intervaly[0]
                    min_y = min(min_y, min(bbox_data.intervaly) - text_height)
                    max_y = max(max_y, max(bbox_data.intervaly) + text_height)
            ax.set_ylim(min_y, max_y)
        if kind == 'bar':
            add_grid_line_at_base_if_needed(ax, 'h')
        if kind == 'barh':
            add_grid_line_at_base_if_needed(ax, 'v')
        rotate_xticklabels_if_not_numeric(ax)

    return ax


def get_description_of_plot_creation(df, fig_filename, kwargs, is_html: bool = True,
                                     should_format: bool = False,
                                     max_rows_and_columns_to_show: Tuple[Optional[int], Optional[int]] = (None, None)
                                     ) -> str:
    """
    Get a description of how the plot was created.
    This is what the LLM will get. This is essentially how the LLM "sees" the figure.
    More sophisticated implementations can be added in the future.
    """
    max_rows_to_show, max_columns_to_show = max_rows_and_columns_to_show
    if is_html:
        len_df = len(df)
        too_long = not is_lower_eq(len_df, max_rows_to_show)
        if too_long:
            df = df.head(3)
        df_str = df_to_html_with_value_format(df, border=0, justify='left')
        if too_long:
            df_str += f'<br>... total {len_df} rows\n'
    else:
        with OnStrPValue(OnStr.SMALLER_THAN):
            df_str = describe_df(df, should_format=should_format,
                                 max_rows_and_columns_to_show=max_rows_and_columns_to_show)

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
