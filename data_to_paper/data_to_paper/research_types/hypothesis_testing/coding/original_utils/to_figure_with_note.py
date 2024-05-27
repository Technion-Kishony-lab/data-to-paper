from typing import Optional, Dict, Collection, Union, Tuple

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

from data_to_paper.env import FOLDER_FOR_RUN
from data_to_paper.latex.clean_latex import process_latex_text_and_math
from data_to_paper.research_types.hypothesis_testing.coding.original_utils.add_html_to_latex import add_html_to_latex, \
    convert_to_latex_comment
from data_to_paper.research_types.hypothesis_testing.coding.original_utils.note_and_legend import \
    convert_note_and_legend_to_latex, convert_note_and_legend_to_html
from data_to_paper.run_gpt_code.overrides.dataframes.df_methods import STR_FLOAT_FORMAT
from data_to_paper.run_gpt_code.overrides.dataframes.utils import to_string_with_iterables
from data_to_paper.run_gpt_code.overrides.pvalue import OnStrPValue, OnStr


def get_xy_coordinates_of_df_plot(df, x=None, y=None, kind='line'):
    """
    Plots the DataFrame and retrieves x and y coordinates for each data point using numerical indices.
    """
    # Create the plot
    ax = df.plot(x=x, y=y, kind=kind, legend=False)

    coords = {}
    if kind == 'bar':
        # Handle bar plots
        for col_index, container in enumerate(ax.containers):
            coords[col_index] = {}
            for rect, row_index in zip(container, range(len(df))):
                coords[col_index][row_index] = (rect.get_x() + rect.get_width() / 2, rect.get_height())
    else:
        # Handle line and other plots
        for line, col_index in zip(ax.lines, range(len(df.columns))):
            coords[col_index] = {}
            for x_val, y_val, row_index in zip(line.get_xdata(), line.get_ydata(), range(len(df))):
                coords[col_index][row_index] = (x_val, y_val)

    plt.close()  # Close the plot to avoid display
    return coords


class PValueToStars:
    default_levels = (0.01, 0.001, 0.0001)

    def __init__(self, p_value: Optional[float] = None, levels: Tuple[float] = None):
        self.p_value = p_value
        self.levels = levels or self.default_levels

    def __str__(self):
        return self.convert_to_stars()

    def convert_to_stars(self):
        p_value = self.p_value
        levels = self.levels
        if p_value < levels[2]:
            return '***'
        if p_value < levels[1]:
            return '**'
        if p_value < levels[0]:
            return '*'
        return 'NS'

    def get_conversion_legend_text(self) -> str:
        #  NS p >= 0.01, * p < 0.01, ** p < 0.001, *** p < 0.0001
        levels = self.levels
        legend = [f'NS p >= {levels[0]}']
        for i, level in enumerate(levels):
            legend.append(f'{(i + 1) * "*"} p < {level}')
        return ', '.join(legend)


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
    xerr = _convert_err_and_ci_to_err(df, x, 'x', xerr, x_ci)
    yerr = _convert_err_and_ci_to_err(df, y, 'y', yerr, y_ci)
    df.plot(x=x, y=y, kind=kind, ax=ax, xerr=xerr, yerr=yerr, **kwargs)
    coords = get_xy_coordinates_of_df_plot(df, x=x, y=y, kind=kind)

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
        if y_p_value not in df.columns:
            raise ValueError(f'The p_value column "{x_p_value}" is not in the dataframe.')
        y_p_values = df[y_p_value]
        if yerr is None:
            raise ValueError('The yerr or y_ci argument must be provided when plotting y_p_value.')

        for col_index, index_data in coords.items():
            for row_index, (x, y) in index_data.items():
                # TODO: need to take care of bars with negative values, in which case the text should be below the bar
                ax.text(x, y + yerr[1, row_index], PValueToStars(y_p_values[row_index]).convert_to_stars(),
                        ha='center', va='bottom')


def get_description_of_plot_creation(df, fig_filename, kwargs, float_num_digits=4) -> str:
    """
    Get a description of how the plot was created.
    This is what the LLM will get. This is essentially how the LLM "sees" the figure.
    More sophisticated implementations can be added in the future.
    """
    with OnStrPValue(OnStr.SMALLER_THAN):
        df_str = to_string_with_iterables(df, float_format=STR_FLOAT_FORMAT)

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


def to_figure_with_note(df: pd.DataFrame, filename: Optional[str],
                        caption: str = None,
                        label: str = None,
                        note: str = None,
                        legend: Dict[str, str] = None,
                        float_num_digits: int = 4,
                        pvalue_on_str: Optional[OnStr] = None,
                        comment: str = None,
                        append_html: bool = True,
                        **kwargs):
    """
    Create a matplotlib figure embedded in a LaTeX figure with a caption and label.
    """
    if note:
        caption = f'{caption}\n{note}'
    fig_filename = filename.replace('.tex', '.png')
    fig, ax = plt.subplots()
    with OnStrPValue(OnStr.AS_FLOAT):
        df_plot_with_pvalue(df, ax=ax, **kwargs)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right",
                       rotation_mode="anchor", wrap=True)
    plt.tight_layout()  # Adjusts subplot parameters to give the plot more room
    fig.savefig(fig_filename)

    index = kwargs.get('use_index', True)

    label = r'\label{' + label + '}\n' if label else ''

    caption_and_legend = convert_note_and_legend_to_latex(df, caption, legend, index)
    caption_and_legend_html = convert_note_and_legend_to_html(df, caption, legend, index)

    latex = get_figure_and_caption_as_latex(fig_filename, caption_and_legend, label)
    html = get_figure_and_caption_as_html(fig_filename, caption_and_legend_html)

    latex += convert_to_latex_comment(
        get_description_of_plot_creation(df, fig_filename, kwargs, float_num_digits=float_num_digits))

    if comment:
        latex = comment + '\n' + latex

    if append_html:
        latex = add_html_to_latex(latex, html)

    if filename is not None:
        with open(filename, 'w') as f:
            f.write(latex)
    return latex


def get_figure_and_caption_as_latex(filename: str, caption: str, label: str) -> str:
    """
    Save a figure with a caption and label.
    """
    caption = process_latex_text_and_math(caption)
    latex = f"""
\\begin{{figure}}[htbp]
\\centering
\\includegraphics[width=0.8\\textwidth]{{{filename}}}
\\caption{{{caption}}}
\\label{{{label}}}
\\end{{figure}}
"""
    return latex


def get_figure_and_caption_as_html(filename: str, caption: str, width: int = None):
    """
    Save a figure with a caption and label.
    """
    if width is None:
        width_str = ''
    else:
        width_str = f'width="{width}"'
    html = f"""
        <div>
        <img src="{FOLDER_FOR_RUN / filename}" alt="{caption}" {width_str} />
        <p>{caption}</p>
        </div>
    """
    return html
