from typing import List


def add_tables_to_paper_section(section_content: str, section_tables: List[str]) -> str:
    """
    Insert the tables into the ready_to_be_tabled_paper_sections.
    """
    for table in section_tables:
        table_label_start = table.find('label{') + len('label{')  # find the start of the label
        if table_label_start == -1:
            table_label = None
        else:
            table_label_end = table.find('}', table_label_start)  # find the end of the label
            table_label = table[table_label_start:table_label_end]  # extract the label
        # find the parag that contains the table reference
        for sentence in section_content.split('\n\n'):
            if table_label is not None and table_label in sentence:
                # add the table after the table reference parag.
                section_content = section_content.replace(sentence, sentence + table)
                break
        else:
            # add the table at the end of the section
            section_content += table
    return section_content
