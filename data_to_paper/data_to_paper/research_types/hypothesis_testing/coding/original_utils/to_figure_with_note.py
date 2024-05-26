from typing import Optional, Dict, Collection

import pandas as pd
from matplotlib import pyplot as plt

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
    for i, level in enumerate(levels[::-1]):
        if p_value < level:
            return '*' * (i + 1)
    return 'NS'


def df_plot_with_pvalue(df, x, y, kind='line', p_value: Optional[str] = None, **kwargs):
    """
    Same as df.plot, but allows for plotting p-values as 'NS', '*', '**', or '***'.
    p_value: A string representing the column name of the p-values.
    """
    df.plot(**kwargs)
    if not p_value:
        return
    if p_value not in df.columns:
        raise ValueError(f'The p_value column "{p_value}" is not in the dataframe.')
    p_values = df[p_value]
    yerr = kwargs.get('yerr', None)
    xerr = kwargs.get('xerr', None)
    if xerr is not None:
        raise ValueError('The xerr argument is not supported when plotting p-values.')
    if yerr is None:
        raise ValueError('The yerr argument must be provided when plotting p-values.')
    yerr = df[yerr]
    if kind in ['line', 'scatter']:
        if x is None:
            raise ValueError('The x argument must be provided when plotting lines or scatter plots.')
        if y is None:
            raise ValueError('The y argument must be provided when plotting lines or scatter plots.')
        for i, (x_val, y_val) in enumerate(zip(df[x], df[y])):
            plt.text(x_val, y_val + yerr[i], convert_p_value_to_stars(p_values[i]))
    else:
        raise ValueError(f'The kind "{kind}" is not supported when plotting p-values.')


def to_figure_with_note(df: pd.DataFrame, filename: Optional[str], caption: str = None, label: str = None,
                        legend: Dict[str, str] = None,
                        float_num_digits: int = 4,
                        pvalue_on_str: Optional[OnStr] = None,
                        comment: str = None,
                        append_html: bool = True,
                        **kwargs):
    """
    Create a matplotlib figure embedded in a LaTeX figure with a caption and label.
    """

    fig, ax = plt.subplots()
    with OnStrPValue(pvalue_on_str):
        df_plot_with_pvalue(df, **kwargs)
    plt.xticks(rotation=0)  # Keeps the x-axis labels horizontal
    plt.tight_layout()  # Adjusts subplot parameters to give the plot more room
    fig.savefig(filename)

    index = kwargs.get('index', True)

    label = r'\label{' + label + '}\n' if label else ''

    caption_and_legend = convert_note_and_legend_to_latex(df, caption, legend, index)
    caption_and_legend_html = convert_note_and_legend_to_html(df, caption, legend, index)

    latex = get_figure_and_caption_as_latex(filename, caption_and_legend, label, should_save=False)
    html = get_figure_and_caption_as_html(filename, caption_and_legend_html, width=200, should_save=False)

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


def get_figure_and_caption_as_latex(filename: str, caption: str, label: str,
                                    should_save: bool = False):
    """
    Save a figure with a caption and label.
    """
    caption = process_latex_text_and_math(caption)
    latex = f"""
        \\begin{{figure}}[htbp]
        \\centering
        \\includegraphics[width=0.8\\textwidth]{{{filename.replace(".png", "")}}}
        \\caption{{{caption}}}
        \\label{{{label}}}
        \\end{{figure}}
    """
    if should_save:
        with open(filename.replace('.png', '.tex'), 'w') as f:
            f.write(latex)
    return latex


def get_figure_and_caption_as_html(filename: str, caption: str, width: int = 200, should_save: bool = False):
    """
    Save a figure with a caption and label.
    """
    html = f"""
        <div>
        <img src="{filename}" alt="{caption}" width="{width}" />
        <p>{caption}</p>
        </div>
    """
    if should_save:
        with open(filename.replace('.png', '.html'), 'w') as f:
            f.write(html)
    return html
