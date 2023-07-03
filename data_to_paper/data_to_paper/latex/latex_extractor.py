from data_to_paper.utils.text_extractors import extract_text_between_tags

from .exceptions import FailedToExtractLatexContent
from .latex_section_tags import get_list_of_tag_pairs_for_section_or_fragment


def extract_latex_section_from_response(response: str, section_or_fragment: str, keep_tags: bool = True):
    """
    Extract specified latex part from chatgpt response.
    Report errors if the latex part is not found or is empty.
    """
    list_of_tag_pairs = get_list_of_tag_pairs_for_section_or_fragment(section_or_fragment)
    for tag_pair in list_of_tag_pairs:
        try:
            return extract_text_between_tags(response, *tag_pair, keep_tags=keep_tags)
        except ValueError:
            pass

    raise FailedToExtractLatexContent(f'Failed to extract {section_or_fragment} from response. '
                                      f'The response does not contain: {list_of_tag_pairs[0]}.')
