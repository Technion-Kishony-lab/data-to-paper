from typing import Optional, Union, Tuple

import matplotlib as mpl
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

from data_to_paper.graphics.matplotlib_utils import get_xy_coordinates_of_df_plot, \
    replace_singleton_legend_with_axis_label, add_grid_line_at_zero_if_not_origin, rotate_xticklabels_if_not_numeric
from data_to_paper.research_types.hypothesis_testing.coding.original_utils.df_to_labeled_latex import \
    df_to_numerically_labeled_latex
from data_to_paper.run_gpt_code.overrides.pvalue import PValueToStars, OnStr


RC_PARAMS = {
    'figure.figsize': [10, 6],
    'font.size': 14,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.facecolor': 'white',
    'axes.facecolor': 'white'
}


def _convert_err_and_ci_to_err(df: pd.DataFrame, xy: Optional[str],
                               xy_name: str,
                               err: Optional[str], ci: Optional[Union[str, Tuple[str, str]]]
                               ) -> Optional[np.ndarray]:
    """
    Create a confidence interval from a dataframe.
    """
    if err is not None:
        if ci is not None:
            raise ValueError(f'The {xy_name}err and {xy_name}_ci arguments cannot be used together.')
        if not isinstance(err, str):
            raise ValueError(f'The {xy_name}err argument must be a string.')
        df = df[err]
        return np.array([df, df])
    if ci is None:
        return None
    if not isinstance(ci, str):
        if not isinstance(ci, (list, tuple)) or len(ci) != 2 or not all(isinstance(x, str) for x in ci):
            raise ValueError(f'The {xy_name}_ci argument must be a str or a list of two strings.')
        ci = list(ci)
    ci = np.vstack(df[ci].to_numpy())
    if ci.shape[1] != 2:
        raise ValueError(f'df[{xy_name}_ci].shape[1] must be 2.')
    if xy is None:
        raise ValueError(f'The {xy_name} argument must be provided when {xy_name}_ci is provided.')
    nominal = df[xy]
    upper = ci[:, 1] - nominal
    lower = nominal - ci[:, 0]
    return np.array([lower, upper])


def df_plot_with_pvalue(df, x=None, y=None, kind='line', ax: Optional[plt.Axes] = None,
                        xerr: Optional[str] = None, yerr: Optional[str] = None,
                        x_ci: Optional[str] = None, y_ci: Optional[str] = None,
                        x_p_value: Optional[str] = None, y_p_value: Optional[str] = None,
                        **kwargs):
    """
    Same as df.plot, but allows for plotting p-values as 'NS', '*', '**', or '***'.
    p_value: A string representing the column name of the p-values.
    """
    with mpl.rc_context(rc=RC_PARAMS):
        xerr = _convert_err_and_ci_to_err(df, x, 'x', xerr, x_ci)
        yerr = _convert_err_and_ci_to_err(df, y, 'y', yerr, y_ci)
        df.plot(x=x, y=y, kind=kind, ax=ax, xerr=xerr, yerr=yerr, **kwargs)
        coords = get_xy_coordinates_of_df_plot(df, x=x, y=y, kind=kind)
        replace_singleton_legend_with_axis_label(ax, kind)
        rotate_xticklabels_if_not_numeric(ax)
        if kind == 'bar':
            add_grid_line_at_zero_if_not_origin(ax, 'h')
        if kind == 'barh':
            add_grid_line_at_zero_if_not_origin(ax, 'v')

        # Add p-values
        if x_p_value is None and y_p_value is None:
            return
        elif x_p_value is not None and y_p_value is not None:
            raise ValueError('Only one of x_p_value and y_p_value can be provided.')
        elif x_p_value is not None:
            # x-values
            # TODO: Implement this
            raise ValueError('The x_p_value argument is currently not supported.')
        else:
            # y-values
            y_p_values = df[y_p_value]
            if yerr is None:
                raise ValueError('The `yerr` or `y_ci` argument must be provided when including `y_p_value`.')
            for col_index, index_data in coords.items():
                for row_index, (x, y) in index_data.items():
                    # TODO: need to take care of bars with negative values, in which case the text should be below
                    #  the bar
                    ax.text(x, y + yerr[1, row_index], PValueToStars(y_p_values[row_index]).convert_to_stars(),
                            ha='center', va='bottom')


def get_description_of_plot_creation(df, fig_filename, kwargs) -> str:
    """
    Get a description of how the plot was created.
    This is what the LLM will get. This is essentially how the LLM "sees" the figure.
    More sophisticated implementations can be added in the future.
    """
    df_str = df_to_numerically_labeled_latex(df, OnStr.SMALLER_THAN)

    kwargs = kwargs.copy()
    ci_x = kwargs.pop('x_ci', None)
    ci_y = kwargs.pop('y_ci', None)
    p_value_x = kwargs.pop('x_p_value', None)
    p_value_y = kwargs.pop('y_p_value', None)

    s = '\n'
    s += f'This latex figure presents "{fig_filename}" which was created from the following df:\n\n'
    s += df_str
    s += '\n\n'
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
        s += f'\n\nThese p-values were presented above the data points as stars:\n'
        s += PValueToStars().get_conversion_legend_text()
    return s
