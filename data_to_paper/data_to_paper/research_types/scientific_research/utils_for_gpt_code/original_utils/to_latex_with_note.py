import re
from contextlib import ExitStack
from typing import Optional, Dict

import pandas as pd

from data_to_paper.latex.clean_latex import replace_special_latex_chars, process_latex_text_and_math
from data_to_paper.run_gpt_code.overrides.pvalue import OnStr, PValue, OnStrPValue
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


def to_latex_with_note(df: pd.DataFrame, filename: Optional[str], caption: str = None, label: str = None,
                       note: str = None,
                       legend: Dict[str, str] = None,
                       is_wide: bool = True,
                       float_num_digits: int = 4,
                       pvalue_on_str: Optional[OnStr] = None,
                       **kwargs):
    """
    Create a latex table with a note.
    Same as df.to_latex, but with a note and legend.
    """

    with OnStrPValue(pvalue_on_str):
        regular_latex_table = df.to_latex(None, caption=None, label=None, **kwargs)

    index = kwargs.get('index', True)

    tabular_part = get_tabular_block(regular_latex_table)
    caption = r'\caption{' + process_latex_text_and_math(caption) + '}\n' if caption else ''
    label = r'\label{' + label + '}\n' if label else ''

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

    template = THREEPARTTABLE if not is_wide else THREEPARTTABLE_WIDE
    latex = template.replace('<tabular>', tabular_part) \
        .replace('<caption>\n', caption) \
        .replace('<label>\n', label) \
        .replace('<note_and_legend>', '\n'.join(note_and_legend))

    if float_num_digits is not None:
        latex = round_floats(latex, float_num_digits, pad_with_spaces=False)

    if filename is not None:
        with open(filename, 'w') as f:
            f.write(latex)
    return latex


def get_tabular_block(latex_table: str) -> str:
    """
    Extract the tabular block of the table.
    """
    return re.search(pattern=r'\\begin{tabular}.*\n(.*)\\end{tabular}', string=latex_table, flags=re.DOTALL).group(0)
