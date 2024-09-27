from typing import Optional, Dict, Tuple, Union, List, Iterable

import pandas as pd
from matplotlib import pyplot as plt
from pathlib import Path

from data_to_paper.latex.clean_latex import process_latex_text_and_math, replace_special_latex_chars
from data_to_paper.run_gpt_code.overrides.pvalue import PValueToStars, convert_p_values_to_floats, \
    pvalue_on_str_for_latex
from data_to_paper.text.text_formatting import escape_html
from data_to_paper.utils.check_type import raise_on_wrong_func_argument_types_decorator
from data_to_paper.utils.multi_process import run_func_in_separate_process
from data_to_paper.run_gpt_code.config import configure_matplotlib

from .df_plot_with_pvalue import df_plot_with_pvalue, get_description_of_plot_creation
from .matplotlib_utils import get_axis_parameters, AxisParameters, fit_fig_to_axes
from .note_and_legend import convert_note_and_glossary_to_html, convert_note_and_glossary_to_latex_figure_caption
from .utils import convert_to_latex_comment, convert_filename_to_label
from .consts import ALLOWED_PLOT_KINDS, FIG_SIZE_INCHES, AXES_SIZE_INCHES, FIG_DPI


@raise_on_wrong_func_argument_types_decorator
def df_to_figure(df: pd.DataFrame, filename: Optional[str],
                 caption: Optional[str] = None,
                 label: Optional[str] = None,
                 note: Optional[str] = None,
                 glossary: Optional[Dict[str, str]] = None,
                 create_fig: bool = False,
                 is_html: bool = False,
                 figure_folder: Optional[Path] = None,
                 should_format: bool = False,
                 max_rows_and_columns_to_show: Tuple[Optional[int], Optional[int]] = (None, None),
                 **kwargs):
    """
    Create a matplotlib figure embedded in a LaTeX figure with a caption and label.
    """
    label = convert_filename_to_label(filename, label)
    label = 'figure:' + label

    fig_filename = filename + '.png'
    figure_path = figure_folder / fig_filename if figure_folder else fig_filename

    kind = kwargs.get('kind', 'bar')
    if kind not in ALLOWED_PLOT_KINDS:
        raise ValueError(f'`kind` must be one of {ALLOWED_PLOT_KINDS}, but got {repr(kind)}.')

    if create_fig:
        create_fig_for_df_to_figure_and_get_axis_parameters(df, filepath=figure_path, **kwargs)

    index = kwargs.get('use_index', True)
    label = label or ''

    glossary = {} if glossary is None else glossary.copy()
    if kwargs.get('x_p_value') or kwargs.get('y_p_value'):
        glossary['Significance'] = PValueToStars().get_conversion_legend_text()

    caption = caption or ''
    if is_html:
        note_and_glossary = convert_note_and_glossary_to_html(df, note, glossary, index)
        caption_note_and_glossary = escape_html(caption) + '<br>' + note_and_glossary
        description = get_description_of_plot_creation(df, fig_filename, kwargs, is_html=True,
                                                       should_format=should_format,
                                                       max_rows_and_columns_to_show=max_rows_and_columns_to_show)
        s = get_figure_and_caption_as_html(figure_path, caption_note_and_glossary.strip())
        s += description
    else:
        note_and_glossary = convert_note_and_glossary_to_latex_figure_caption(df, note, glossary, index)
        caption_note_and_glossary = replace_special_latex_chars(caption) + '\n' + note_and_glossary
        with pvalue_on_str_for_latex():
            description = get_description_of_plot_creation(df, fig_filename, kwargs, is_html=False,
                                                           should_format=should_format,
                                                           max_rows_and_columns_to_show=max_rows_and_columns_to_show)
        s = get_figure_and_caption_as_latex(fig_filename, caption_note_and_glossary.strip(), label)
        s += '\n' + convert_to_latex_comment(description)
    return s


def _replace_with_str_no_underscores(s):
    if s is None:
        return s
    if not isinstance(s, str):
        if isinstance(s, Iterable):
            return type(s)([_replace_with_str_no_underscores(col) for col in s])
        s = str(s)
    return s.replace('_', ' ')


def replace_df_column_names_to_str_with_no_underscores(df: pd.DataFrame, **kwargs):

    # find all the underscores in the column names:
    df = df.copy()
    df.columns = _replace_with_str_no_underscores(df.columns)

    for arg in ['x', 'y', 'yerr', 'xerr', 'x_ci', 'y_ci', 'x_p_value', 'y_p_value']:
        if arg in kwargs:
            kwargs[arg] = _replace_with_str_no_underscores(kwargs[arg])
    return df, kwargs


def run_create_fig_for_df_to_figure_and_get_axis_parameters(df: pd.DataFrame, filepath: Optional[Path] = None,
                                                            in_separate_process: bool = True, **kwargs) -> List[str]:
    """
    Run the `create_fig_for_df_to_figure` function in a separate process.
    Otherwise we get killing of the kernel due to matplotlib issues.
    """
    return run_func_in_separate_process(create_fig_for_df_to_figure_and_get_axis_parameters, df, filepath,
                                        in_separate_process=in_separate_process, **kwargs)


def create_fig_for_df_to_figure_and_get_axis_parameters(df: pd.DataFrame, filepath: Optional[Path] = None,
                                                        **kwargs) -> AxisParameters:
    configure_matplotlib()

    # The figure size in inches is not consequential, because we use fit_fig_to_axes
    fig = plt.figure(figsize=FIG_SIZE_INCHES, dpi=FIG_DPI.val)

    ax = fig.add_axes((0.1, 0.1, AXES_SIZE_INCHES[0] / FIG_SIZE_INCHES[0], AXES_SIZE_INCHES[1] / FIG_SIZE_INCHES[1]))

    df = convert_p_values_to_floats(df.copy())

    # Replace underscores with spaces in the column names.
    # Otherwise df.plot() may skip the column with underscores in the name.
    df, kwargs = replace_df_column_names_to_str_with_no_underscores(df, **kwargs)

    df_plot_with_pvalue(df, ax=ax, **kwargs)

    # Adjusts subplot parameters to give the plot more room
    fit_fig_to_axes(fig, fit_width=True, fit_height=True, margin_pixels=10)

    if filepath:
        fig.savefig(filepath)

    axis_parameters = get_axis_parameters(ax)

    # figure cleanup
    ax.clear()
    fig.clear()
    plt.close(fig)
    plt.close('all')

    return axis_parameters


def get_figure_and_caption_as_latex(filename: str, caption: str, label: str) -> str:
    """
    Save a figure with a caption and label.
    """
    caption = process_latex_text_and_math(caption)
    latex = f"""
\\begin{{figure}}[htbp]
\\centering
\\includegraphics{{{filename}}}
\\caption{{{caption}}}
\\label{{{label}}}
\\end{{figure}}
"""
    return latex.strip()


def get_figure_and_caption_as_html(filepath: Union[str, Path], caption: str, width: int = 750):
    """
    Save a figure with a caption and label.
    """
    if width is None:
        width_str = ''
    else:
        width_str = f'width="{width}"'
    html = f"""
        <div>
        <img src="{filepath}" alt="{caption}" {width_str} />
        <p>{caption}</p>
        </div>
    """
    return html
