import re
from typing import Optional, Dict

import pandas as pd

from data_to_paper.latex.clean_latex import replace_special_latex_chars, process_latex_text_and_math
from data_to_paper.research_types.hypothesis_testing.coding.original_utils.add_html_to_latex import add_html_to_latex
from data_to_paper.research_types.hypothesis_testing.coding.original_utils.note_and_legend import \
    convert_note_and_glossary_to_latex_table_caption, convert_note_and_glossary_to_html
from data_to_paper.run_gpt_code.overrides.dataframes.df_methods import STR_FLOAT_FORMAT
from data_to_paper.run_gpt_code.overrides.dataframes.utils import to_latex_with_value_format, to_html_with_value_format
from data_to_paper.run_gpt_code.overrides.pvalue import OnStr, OnStrPValue
from data_to_paper.utils.text_numeric_formatting import round_floats
from data_to_paper.utils.dataframe import extract_df_axes_labels

THREEPARTTABLE = r"""\begin{table}[htbp]
\centering
\begin{threeparttable}
<caption>
<label>
<tabular>
\begin{tablenotes}
<note_and_glossary>
\end{tablenotes}
\end{threeparttable}
\end{table}
"""

THREEPARTTABLE_WIDE = r"""\begin{table}[h]
<caption>
<label>
\begin{threeparttable}
\renewcommand{\TPTminimum}{\linewidth}
\makebox[\linewidth]{%
<tabular>}
\begin{tablenotes}
\footnotesize
<note_and_glossary>
\end{tablenotes}
\end{threeparttable}
\end{table}
"""


HTML_TABLE_WITH_LABEL_AND_CAPTION = r"""
<b>{caption}</b>
{table}
{note_and_glossary}
"""


def raise_on_wrong_params_for_to_latex_with_note(df: pd.DataFrame, filename: Optional[str],
                                                 caption: str = None,
                                                 label: str = None,
                                                 note: str = None,
                                                 glossary: Dict[str, str] = None,
                                                 is_wide: bool = True,
                                                 pvalue_on_str: Optional[OnStr] = None,
                                                 comment: str = None,
                                                 append_html: bool = True,
                                                 **kwargs):
    if not isinstance(df, pd.DataFrame):
        raise ValueError(f'Expected `df` to be a pandas.DataFrame, got {type(df)}')

    if filename is not None:
        if not isinstance(filename, str):
            raise ValueError(f'Expected `filename` to be a string, got {type(filename)}')
        if not filename.endswith('.tex'):
            raise ValueError(f'Expected `filename` to end with .tex, got {filename}')

    if not isinstance(caption, str) and caption is not None:
        raise ValueError(f'Expected `caption` to be a string or None, got {type(caption)}')

    if not isinstance(label, str) and label is not None:
        raise ValueError(f'Expected `label` to be a string or None, got {type(label)}')

    if not isinstance(note, str) and note is not None:
        raise ValueError(f'Expected `note` to be a string or None, got {type(note)}')

    if isinstance(glossary, dict):
        if not all(isinstance(key, str) for key in glossary.keys()):
            raise ValueError(f'Expected `glossary` keys to be strings, got {glossary.keys()}')
        if not all(isinstance(value, str) for value in glossary.values()):
            raise ValueError(f'Expected `glossary` values to be strings, got {glossary.values()}')
    elif glossary is not None:
        raise ValueError(f'Expected `glossary` to be a dict or None, got {type(glossary)}')

    if not isinstance(is_wide, bool):
        raise ValueError(f'Expected `is_wide` to be a bool, got {type(is_wide)}')

    if not isinstance(comment, str) and comment is not None:
        raise ValueError(f'Expected `comment` to be a string or None, got {type(comment)}')

    if not isinstance(append_html, bool):
        raise ValueError(f'Expected `append_html` to be a bool, got {type(append_html)}')


def to_latex_with_note(df: pd.DataFrame, filename: Optional[str], caption: str = None, label: str = None,
                       note: str = None,
                       glossary: Dict[str, str] = None,
                       is_wide: bool = True,
                       pvalue_on_str: Optional[OnStr] = None,
                       comment: str = None,
                       append_html: bool = True,
                       **kwargs):
    """
    Create a latex table with a note.
    Same as df.to_latex, but with a note and glossary.
    """

    raise_on_wrong_params_for_to_latex_with_note(df, filename, caption, label, note, glossary, is_wide,
                                                 pvalue_on_str, comment, append_html, **kwargs)

    with OnStrPValue(pvalue_on_str):
        # Label the numeric values with @@<...>@@ - to allow converting to ReferenceableText:
        regular_latex_table = to_latex_with_value_format(
            df, numeric_formater=lambda x: '@@<' + STR_FLOAT_FORMAT(x) + '>@@', caption=None, label=None, **kwargs)

    pvalue_on_str_html = OnStr.SMALLER_THAN if pvalue_on_str == OnStr.LATEX_SMALLER_THAN else pvalue_on_str
    with OnStrPValue(pvalue_on_str_html):
        regular_html_table = to_html_with_value_format(df, border=0, justify='left')

    tabular_part = get_tabular_block(regular_latex_table)
    latex_caption = r'\caption{' + process_latex_text_and_math(caption) + '}\n' if caption else ''
    html_caption = caption if caption else ''
    label = r'\label{' + label + '}\n' if label else ''

    index = kwargs.get('index', True)
    note_and_glossary = convert_note_and_glossary_to_latex_table_caption(df, note, glossary, index)
    note_and_glossary_html = convert_note_and_glossary_to_html(df, note, glossary, index)

    template = THREEPARTTABLE if not is_wide else THREEPARTTABLE_WIDE
    latex = template.replace('<tabular>', tabular_part) \
        .replace('<caption>\n', latex_caption) \
        .replace('<label>\n', label) \
        .replace('<note_and_glossary>', note_and_glossary)

    html = HTML_TABLE_WITH_LABEL_AND_CAPTION.replace('{caption}', html_caption) \
        .replace('{table}', regular_html_table) \
        .replace('{note_and_glossary}', note_and_glossary_html)

    if comment:
        latex = comment + '\n' + latex

    if append_html:
        latex = add_html_to_latex(latex, html)

    if filename is not None:
        with open(filename, 'w') as f:
            f.write(latex)
    return latex


def get_tabular_block(latex_table: str) -> str:
    """
    Extract the tabular block of the table.
    """
    return re.search(pattern=r'\\begin{tabular}.*\n(.*)\\end{tabular}', string=latex_table, flags=re.DOTALL).group(0)

