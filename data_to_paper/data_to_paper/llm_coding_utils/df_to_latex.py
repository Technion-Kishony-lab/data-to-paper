import re
from typing import Optional, Dict

import pandas as pd
from pathlib import Path

from data_to_paper.latex.clean_latex import process_latex_text_and_math
from data_to_paper.run_gpt_code.overrides.dataframes.utils import df_to_html_with_value_format
from data_to_paper.run_gpt_code.overrides.pvalue import pvalue_on_str_for_latex
from data_to_paper.utils.check_type import raise_on_wrong_func_argument_types_decorator

from .describe import df_to_numerically_labeled_latex
from .note_and_legend import convert_note_and_glossary_to_latex_table_caption, \
    convert_note_and_glossary_to_html
from .utils import convert_filename_to_label

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
<style>
    thead th {
        text-align: left;  /* Align the column headers to the left */
    }
    tbody th {
        text-align: left;  /* Align the row headers (index) to the left */
    }
</style>
{table}
{note_and_glossary}
"""


@raise_on_wrong_func_argument_types_decorator
def df_to_latex(df: pd.DataFrame, filename: Optional[str],
                caption: Optional[str] = None,
                label: Optional[str] = None,
                note: Optional[str] = None,
                glossary: Optional[Dict[str, str]] = None,
                is_wide: bool = True,
                is_html: Optional[bool] = False,
                figure_folder: Optional[Path] = None,  # needed for compatibility with df_to_figure
                should_format: bool = False,
                **kwargs):
    """
    Create a latex table with a note.
    Same as df.to_latex, but with a note and glossary.
    is_html: If True, return an HTML table instead of a LaTeX table.
        if False, return a LaTeX table.
        if None, do nothing. (used to raise on wrong argument types)
    """
    label = convert_filename_to_label(filename, label)
    label = 'table:' + label

    index = kwargs.get('index', True)
    if is_html is True:
        html_caption = caption if caption else ''
        regular_html_table = df_to_html_with_value_format(df, border=0, justify='left', **kwargs)
        note_and_glossary_html = convert_note_and_glossary_to_html(df, note, glossary, index)
        return HTML_TABLE_WITH_LABEL_AND_CAPTION.replace('{caption}', html_caption) \
            .replace('{table}', regular_html_table) \
            .replace('{note_and_glossary}', note_and_glossary_html)

    if is_html is False:
        with pvalue_on_str_for_latex():
            regular_latex_table = df_to_numerically_labeled_latex(df, should_format=should_format, **kwargs)
        tabular_part = get_tabular_block(regular_latex_table)
        latex_caption = r'\caption{' + process_latex_text_and_math(caption) + '}\n' if caption else ''
        label = r'\label{' + label + '}\n' if label else ''

        note_and_glossary = convert_note_and_glossary_to_latex_table_caption(df, note, glossary, index)

        template = THREEPARTTABLE if not is_wide else THREEPARTTABLE_WIDE
        latex = template.replace('<tabular>', tabular_part) \
            .replace('<caption>\n', latex_caption) \
            .replace('<label>\n', label) \
            .replace('<note_and_glossary>', note_and_glossary)

        return latex


def get_tabular_block(latex_table: str) -> str:
    """
    Extract the tabular block of the table.
    """
    return re.search(pattern=r'\\begin{tabular}.*\n(.*)\\end{tabular}', string=latex_table, flags=re.DOTALL).group(0)
