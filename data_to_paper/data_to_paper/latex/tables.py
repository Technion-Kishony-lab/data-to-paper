import re
from typing import List, Optional, Dict

from data_to_paper.latex.clean_latex import replace_special_latex_chars


def get_table_label(latex_table: str) -> Optional[str]:
    """
    Extract the label of the table.
    """
    pattern = r'\\label{([^{}]+)}'
    match = re.search(pattern, latex_table)
    if match:
        return match.group(1)


def get_table_caption(latex_table: str) -> Optional[str]:
    """
    Extract the caption of the table.
    """
    pattern = r'\\caption{([^{}]+)}'
    match = re.search(pattern, latex_table)
    if match:
        return match.group(1)


def get_table_column_headers(latex_table: str) -> Optional[List[str]]:
    """
    Extract the column headers of the table.
    """
    pattern = r'\\toprule\n(.+?) \\\\\n\\midrule'
    header_rows = re.findall(pattern, latex_table, re.DOTALL)
    if not header_rows:
        return None
    return header_rows[0].split(' & ')[1:]


def get_table_row_names(latex_table):
    row_pattern = r'\\textbf{([^}]+)}'
    row_names = re.findall(row_pattern, latex_table)
    return row_names


def add_tables_to_paper_section(section_content: str, section_tables: List[str]) -> str:
    """
    Insert the tables into the ready_to_be_tabled_paper_sections.
    """
    for table in section_tables:
        table_label = get_table_label(table)
        # find the paragraph that contains the table reference
        for paragraph in section_content.split('\n\n'):
            if table_label is not None and table_label in paragraph:
                # add the table after the table reference paragraph.
                section_content = section_content.replace(paragraph, paragraph + table)
                break
        else:
            # add the table at the end of the section
            section_content += table
    return section_content


THREEPARTTABLE = r"""\begin{table}[htbp]
\centering
\begin{threeparttable}
<caption><label><tabular>
\begin{tablenotes}
<note_and_legend>
\end{tablenotes}
\end{threeparttable}
\end{table}
"""


THREEPARTTABLE_WIDE = r"""\begin{table}[h]<caption><label>
\begin{threeparttable}
\renewcommand{\TPTminimum}{\linewidth}
\makebox[\linewidth]{%
<tabular>}
\begin{tablenotes}
\small
<note_and_legend>
\end{tablenotes}
\end{threeparttable}
\end{table}
"""


def create_threeparttable(regular_latex_table: str, note: str, legend: Dict[str, str] = None,
                          is_wide: bool = True) -> str:
    """
    Create a threeparttable from a regular latex table.
    Add a note to the table.
    """

    # use regex to extract the tabular part of the table from '\begin{tabular}' to '\end{tabular}'
    tabular_part = re.search(pattern=r'\\begin{tabular}.*\n(.*)\\end{tabular}', string=regular_latex_table,
                             flags=re.DOTALL).group(0)
    caption = get_table_caption(regular_latex_table)
    if caption is None:
        caption = ''
    else:
        caption = r'\caption{' + caption + '}'

    label = get_table_label(regular_latex_table)
    if label is None:
        label = ''
    else:
        label = r'\label{' + label + '}'

    note_and_legend = ''
    if note:
        note_and_legend += r'\item ' + replace_special_latex_chars(note) + '\n'
    if legend:
        for key, value in legend.items():
            note_and_legend += r'\item ' + replace_special_latex_chars(key) + \
                               ': ' + replace_special_latex_chars(value) + '\n'
    template = THREEPARTTABLE if not is_wide else THREEPARTTABLE_WIDE
    return template.replace('<tabular>', tabular_part) \
        .replace('<caption>', caption) \
        .replace('<label>', label) \
        .replace('<note_and_legend>', note_and_legend)
