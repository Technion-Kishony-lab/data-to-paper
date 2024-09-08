from typing import List, Optional

from data_to_paper.utils import extract_text_between_tags


def get_table_label(latex_table: str) -> Optional[str]:
    """
    Extract the label of the table.
    """
    return extract_text_between_tags(latex_table, '\\label{', '}', keep_tags=False)


def get_table_caption(latex_table: str) -> Optional[str]:
    """
    Extract the caption of the table.
    """
    return extract_text_between_tags(latex_table, '\\caption{', '}', keep_tags=False)


def add_tables_to_paper_section(section_content: str, section_tables: List[str]) -> str:
    """
    Insert the tables into the ready_to_be_tabled_paper_sections.
    """
    paragraphs = section_content.split('\n\n')
    table_paragraph_numbers = []
    for table in section_tables:
        table_label = get_table_label(table)
        # find the paragraph that contains the table reference
        for num, paragraph in enumerate(paragraphs):
            if table_label is not None and table_label in paragraph:
                # add the table after the table reference paragraph.
                table_paragraph_numbers.append(num)
                break
        else:
            # add the table at the end of the last paragraph.
            table_paragraph_numbers.append(len(paragraphs) - 1)
    for table_paragraph_number, table in zip(table_paragraph_numbers, section_tables):
        paragraphs[table_paragraph_number] += '\n\n' + table
    return '\n\n'.join(paragraphs)
