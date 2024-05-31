from typing import Optional, Dict

import pandas as pd
from matplotlib import pyplot as plt

from data_to_paper.env import FOLDER_FOR_RUN
from data_to_paper.graphics.df_plot_with_pvalue import df_plot_with_pvalue, get_description_of_plot_creation
from data_to_paper.graphics.matplotlib_utils import rotate_xticklabels_if_not_numeric, \
    raise_if_numeric_axes_do_not_have_labels
from data_to_paper.latex.clean_latex import process_latex_text_and_math, replace_special_latex_chars
from data_to_paper.research_types.hypothesis_testing.coding.original_utils.add_html_to_latex import add_html_to_latex, \
    convert_to_latex_comment
from data_to_paper.research_types.hypothesis_testing.coding.original_utils.note_and_legend import \
    convert_note_and_glossary_to_html, convert_note_and_glossary_to_latex_figure_caption
from data_to_paper.run_gpt_code.overrides.pvalue import OnStrPValue, OnStr, PValueToStars
from data_to_paper.utils.text_formatting import escape_html


def df_to_figure(df: pd.DataFrame, filename: Optional[str],
                 caption: str = None,
                 label: str = None,
                 note: str = None,
                 glossary: Dict[str, str] = None,
                 pvalue_on_str: Optional[OnStr] = None,
                 comment: str = None,
                 append_html: bool = True,
                 xlabel: Optional[str] = None,
                 ylabel: Optional[str] = None,
                 **kwargs):
    """
    Create a matplotlib figure embedded in a LaTeX figure with a caption and label.
    """
    fig_filename = filename.replace('.tex', '.png')
    fig, ax = plt.subplots()
    with OnStrPValue(OnStr.AS_FLOAT):
        df_plot_with_pvalue(df, ax=ax, xlabel=xlabel, ylabel=ylabel, **kwargs)
    rotate_xticklabels_if_not_numeric(ax)
    raise_if_numeric_axes_do_not_have_labels(ax)
    plt.tight_layout()  # Adjusts subplot parameters to give the plot more room
    fig.savefig(fig_filename)

    index = kwargs.get('use_index', True)

    label = label or ''

    glossary = {} if glossary is None else glossary
    if 'x_p_value' in kwargs or 'y_p_value' in kwargs:
        glossary['Significance'] = PValueToStars().get_conversion_legend_text()

    note_and_glossary = convert_note_and_glossary_to_latex_figure_caption(df, note, glossary, index)
    note_and_glossary_html = convert_note_and_glossary_to_html(df, note, glossary, index)

    caption = caption or ''
    caption_note_and_glossary = replace_special_latex_chars(caption) + '\n' + note_and_glossary
    caption_note_and_glossary_html = escape_html(caption) + '<br>' + note_and_glossary_html

    latex = get_figure_and_caption_as_latex(fig_filename, caption_note_and_glossary, label)
    html = get_figure_and_caption_as_html(fig_filename, caption_note_and_glossary_html)

    latex += convert_to_latex_comment(
        get_description_of_plot_creation(df, fig_filename, kwargs))

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
    return latex.strip()


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
