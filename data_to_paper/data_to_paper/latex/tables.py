import re
from typing import List, Optional


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
