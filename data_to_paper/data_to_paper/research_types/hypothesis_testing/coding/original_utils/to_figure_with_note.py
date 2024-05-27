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
from data_to_paper.run_gpt_code.overrides.dataframes.utils import to_string_with_iterables
from data_to_paper.run_gpt_code.overrides.pvalue import OnStrPValue, OnStr


def convert_p_value_to_stars(p_value: float, levels: Collection[float] = (0.01, 0.001, 0.0001)) -> str:
    """
    Convert a p-value to stars, or 'NS'.
    """
    if p_value < levels[2]:
        return '***'
    if p_value < levels[1]:
        return '**'
    if p_value < levels[0]:
        return '*'
    return 'NS'


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
        if kind in ['line', 'scatter']:
            if x is None:
                raise ValueError('The x argument must be provided when plotting lines or scatter plots.')
            if y is None:
                raise ValueError('The y argument must be provided when plotting lines or scatter plots.')
            for i, (x_val, y_val) in enumerate(zip(df[x], df[y])):
                ax.text(x_val, y_val + yerr[i, 1], convert_p_value_to_stars(y_p_values[i]))
        elif kind == 'bar':
            for i, (x_val, y_val) in enumerate(zip(df.index, df[y])):
                ax.text(x_val, y_val + yerr[i, 1], convert_p_value_to_stars(y_p_values[i]))
        else:
            raise ValueError(f'The kind "{kind}" is not supported when plotting p-values.')


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

    # add the dataframes to the latex as a comment
    with OnStrPValue(pvalue_on_str):
        df_str = to_string_with_iterables(df, float_format=f'.{float_num_digits}f' if float_num_digits else None)
    s = ''
    s += f'This figure was created from the following df:\n\n'
    s += df_str
    s += '\n\n'
    s += f'This df was plotted with the following command:\n\n'
    s += f'df.plot(**{kwargs})'
    latex += convert_to_latex_comment(s)

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
