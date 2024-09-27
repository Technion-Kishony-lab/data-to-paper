from typing import List, Optional

from data_to_paper.text.text_extractors import extract_text_between_tags


def get_displayitem_label(displayitem: str) -> Optional[str]:
    """
    Extract the label of a LaTeX display item (table, figure, etc.).
    """
    return extract_text_between_tags(displayitem, '\\label{', '}', keep_tags=False)


def get_displayitem_caption(displayitem: str, first_line_only: bool = False) -> Optional[str]:
    """
    Extract the caption of a floating LaTeX display item (table, figure, etc.).
    """
    caption = extract_text_between_tags(displayitem, '\\caption{', '}', keep_tags=False)
    if first_line_only:
        caption = caption.split('\n')[0]
    return caption


def add_displayitems_to_paper_section(section_content: str, displayitems: List[str]) -> str:
    """
    Insert the floating elements into the section content.
    """
    paragraphs = section_content.split('\n\n')
    displayitem_paragraph_numbers = []
    for displayitem in displayitems:
        displayitem_label = get_displayitem_label(displayitem)
        # find the paragraph that contains the displayitem reference
        for num, paragraph in enumerate(paragraphs):
            if displayitem_label is not None and displayitem_label in paragraph:
                # add the displayitem after the reference paragraph.
                displayitem_paragraph_numbers.append(num)
                break
        else:
            # add the displayitem at the end of the last paragraph.
            displayitem_paragraph_numbers.append(len(paragraphs) - 1)
    for displayitem_paragraph_number, displayitem in zip(displayitem_paragraph_numbers, displayitems):
        paragraphs[displayitem_paragraph_number] += '\n\n' + displayitem
    return '\n\n'.join(paragraphs)
