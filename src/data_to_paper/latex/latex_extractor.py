from typing import List

from data_to_paper.text.text_extractors import extract_text_between_tags

from .exceptions import FailedToExtractLatexContent
from .latex_section_tags import get_list_of_tag_pairs_for_section_or_fragment

# ChatGPT sometimes adds these to the end of the latex, so we remove them.
REMOVE_FROM_END = [r'\end{document}']


def extract_latex_section_from_response(response: str, section_or_fragment: str, keep_tags: bool = True,
                                        remove_from_end: List[str] = None):
    """
    Extract specified latex part from the LLM response.
    Report errors if the latex part is not found or is empty.
    """
    if remove_from_end is None:
        remove_from_end = REMOVE_FROM_END
    list_of_tag_pairs = get_list_of_tag_pairs_for_section_or_fragment(section_or_fragment)
    for tag_pair in list_of_tag_pairs:
        try:
            latex = extract_text_between_tags(response, *tag_pair, keep_tags=keep_tags, case_sensitive=False)
            break
        except ValueError:
            pass
    else:
        raise FailedToExtractLatexContent(f'Failed to extract {section_or_fragment} from response. '
                                          f'The response does not contain: {list_of_tag_pairs[0]}.')

    latex = latex.strip()
    for remove in remove_from_end:
        if latex.endswith(remove):
            latex = latex[:-len(remove)]
    return latex
