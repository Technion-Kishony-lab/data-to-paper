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


BEGIN_THREEPARTTABLE = r"""\begin{table}[htbp]
\centering
\begin{threeparttable}
"""

END_THREEPARTTABLE = r"""\begin{tablenotes}
<note_and_legend>
\end{tablenotes}
\end{threeparttable}
\end{table}
"""


def create_threeparttable(regular_latex_table: str, note: str, legend: Dict[str, str] = None) -> str:
    """
    Create a threeparttable from a regular latex table.
    Add a note to the table.
    """
    regular_latex_table = re.sub(pattern=r'\\begin{table}.*\n', repl='', string=regular_latex_table)
    regular_latex_table = re.sub(pattern=r'\\end{table}.*\n', repl='', string=regular_latex_table)

    note_and_legend = ''
    if note:
        note_and_legend += r'\item ' + replace_special_latex_chars(note) + '\n'
    if legend:
        for key, value in legend.items():
            note_and_legend += r'\item[' + key + '] ' + replace_special_latex_chars(value) + '\n'

    return BEGIN_THREEPARTTABLE + regular_latex_table + END_THREEPARTTABLE.replace('<note_and_legend>', note_and_legend)
