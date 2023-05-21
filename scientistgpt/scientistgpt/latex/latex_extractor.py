from scientistgpt.utils.text_extractors import extract_text_between_tags

from .exceptions import FailedToExtractLatexContent
from .latex_section_tags import get_list_of_tag_pairs_for_section_or_fragment


def extract_latex_section_from_response(response: str, section_or_fragment: str, as_latex: bool = True):
    """
    Extract specified latex part from chatgpt response.
    Report errors if the latex part is not found or is empty.
    """
    list_of_tag_pairs = get_list_of_tag_pairs_for_section_or_fragment(section_or_fragment)
    for tag_pair in list_of_tag_pairs:
        try:
            content = extract_text_between_tags(response, *tag_pair)
        except ValueError:
            pass
        else:
            if content == '':
                raise FailedToExtractLatexContent(f'The provided {section_or_fragment} is empty.')

            # TODO: we should try to format the latex and report formatting errors to chatgpt
            if as_latex:
                return tag_pair[0] + content + (tag_pair[1] or '')
            return content

    raise FailedToExtractLatexContent(f'Failed to extract {section_or_fragment} from response. '
                                      f'The response does not contain: {list_of_tag_pairs[0]}.')
