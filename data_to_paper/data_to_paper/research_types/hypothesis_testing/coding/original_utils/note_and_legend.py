from typing import Dict

from data_to_paper.latex.clean_latex import replace_special_latex_chars
from data_to_paper.utils.dataframe import extract_df_axes_labels


def convert_note_and_legend_to_latex(df, note: str, legend: Dict[str, str], index: bool) -> str:
    """
    Convert a note and legend to a latex string.
    """
    note_and_legend = []
    if note:
        note_and_legend.append(r'\item ' + replace_special_latex_chars(note))
    if legend:
        axes_labels = extract_df_axes_labels(df, index=index)
        for key, value in legend.items():
            if key in axes_labels:
                note_and_legend.append(r'\item \textbf{' + replace_special_latex_chars(key) +
                                       '}: ' + replace_special_latex_chars(value))
    if len(note_and_legend) == 0:
        note_and_legend.append(r'\item ')  # add an empty item to avoid an error
    return '\n'.join(note_and_legend)


def convert_note_and_legend_to_html(df, note: str, legend: Dict[str, str], index: bool) -> str:
    """
    Convert a note and legend to an html string.
    """
    note_and_legend = []
    if note:
        note_and_legend.append(f'{note}<br>')
    if legend:
        axes_labels = extract_df_axes_labels(df, index=index)
        for key, value in legend.items():
            if key in axes_labels:
                note_and_legend.append(f'<b>{key}</b>: {value}<br>')
    return '\n'.join(note_and_legend)
