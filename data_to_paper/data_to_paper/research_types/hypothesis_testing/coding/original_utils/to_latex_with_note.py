import re
from typing import Optional, Dict

import pandas as pd

from data_to_paper.latex.clean_latex import replace_special_latex_chars, process_latex_text_and_math
from data_to_paper.research_types.hypothesis_testing.coding.original_utils.add_html_to_latex import add_html_to_latex
from data_to_paper.research_types.hypothesis_testing.coding.original_utils.note_and_legend import \
    convert_note_and_legend_to_latex, convert_note_and_legend_to_html
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
<note_and_legend>
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
<note_and_legend>
\end{tablenotes}
\end{threeparttable}
\end{table}
"""


HTML_TABLE_WITH_LABEL_AND_CAPTION = r"""
<b>{caption}</b>
{table}
{note_and_legend}
"""


def to_latex_with_note(df: pd.DataFrame, filename: Optional[str], caption: str = None, label: str = None,
                       note: str = None,
                       legend: Dict[str, str] = None,
                       is_wide: bool = True,
                       float_num_digits: int = 4,
                       pvalue_on_str: Optional[OnStr] = None,
                       comment: str = None,
                       append_html: bool = True,
                       **kwargs):
    """
    Create a latex table with a note.
    Same as df.to_latex, but with a note and legend.
    """
    with OnStrPValue(pvalue_on_str):
        regular_latex_table = df.to_latex(None, caption=None, label=None, multirow=False, multicolumn=False, **kwargs)

    pvalue_on_str_html = OnStr.SMALLER_THAN if pvalue_on_str == OnStr.LATEX_SMALLER_THAN else pvalue_on_str
    with OnStrPValue(pvalue_on_str_html):
        regular_html_table = df.to_html(None, border=0, justify='left')

    tabular_part = get_tabular_block(regular_latex_table)
    latex_caption = r'\caption{' + process_latex_text_and_math(caption) + '}\n' if caption else ''
    html_caption = caption if caption else ''
    label = r'\label{' + label + '}\n' if label else ''

    index = kwargs.get('index', True)
    note_and_legend = convert_note_and_legend_to_latex(df, note, legend, index)
    note_and_legend_html = convert_note_and_legend_to_html(df, note, legend, index)

    template = THREEPARTTABLE if not is_wide else THREEPARTTABLE_WIDE
    latex = template.replace('<tabular>', tabular_part) \
        .replace('<caption>\n', latex_caption) \
        .replace('<label>\n', label) \
        .replace('<note_and_legend>', note_and_legend)

    html = HTML_TABLE_WITH_LABEL_AND_CAPTION.replace('{caption}', html_caption) \
        .replace('{table}', regular_html_table) \
        .replace('{note_and_legend}', note_and_legend_html)

    if float_num_digits is not None:
        latex = round_floats(latex, float_num_digits, source_precision=float_num_digits + 1, pad_with_spaces=False)
        html = round_floats(html, float_num_digits, source_precision=float_num_digits + 1, pad_with_spaces=False)

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

