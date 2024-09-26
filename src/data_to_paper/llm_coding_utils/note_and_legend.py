from typing import Dict

from data_to_paper.latex.clean_latex import replace_special_latex_chars
from data_to_paper.utils.dataframe import extract_df_axes_labels
from data_to_paper.text.text_formatting import escape_html


def convert_note_and_glossary_to_latex_table_caption(df, note: str, glossary: Dict[str, str], index: bool) -> str:
    """
    Convert a note and glossary to a latex string.
    """
    note_and_glossary = []
    if note:
        note_and_glossary.append(r'\item ' + replace_special_latex_chars(note))
    if glossary:
        axes_labels = extract_df_axes_labels(df, index=index)
        for key, value in glossary.items():
            if key in axes_labels or key == 'Significance':
                note_and_glossary.append(r'\item \textbf{' + replace_special_latex_chars(key) +
                                         '}: ' + replace_special_latex_chars(value))
    if len(note_and_glossary) == 0:
        note_and_glossary.append(r'\item ')  # add an empty item to avoid an error
    return '\n'.join(note_and_glossary)


def convert_note_and_glossary_to_latex_figure_caption(df, note: str, glossary: Dict[str, str], index: bool) -> str:
    note_and_glossary = []
    if note:
        note_and_glossary.append(replace_special_latex_chars(note))
    if glossary:
        axes_labels = extract_df_axes_labels(df, index=index)
        for key, value in glossary.items():
            if key in axes_labels or key == 'Significance':
                note_and_glossary.append((replace_special_latex_chars(key) +
                                          ': ' + replace_special_latex_chars(value)).strip())
    # add '. ' at the end of each line if missing:
    note_and_glossary = [line + ' ' if line.endswith('.') else line + '. ' for line in note_and_glossary]
    return '\n'.join(note_and_glossary)


def convert_note_and_glossary_to_html(df, note: str, glossary: Dict[str, str], index: bool) -> str:
    """
    Convert a note and glossary to an html string.
    """
    note_and_glossary = []
    if note:
        note_and_glossary.append(f'{escape_html(note)}<br>')
    if glossary:
        axes_labels = extract_df_axes_labels(df, index=index)
        for key, value in glossary.items():
            if key in axes_labels or key == 'Significance':
                note_and_glossary.append(f'<b>{escape_html(key)}</b>: {escape_html(value)}<br>')
    return '\n'.join(note_and_glossary)
