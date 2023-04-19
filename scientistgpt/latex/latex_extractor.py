from scientistgpt.utils.text_utils import extract_text_between_tags

from .exceptions import FailedToExtractLatexContent
from .latex_section_tags import get_list_of_tag_pairs_for_section


def extract_latex_section_from_response(response: str, section: str):
    """
    Extract specified latex part from chatgpt response.
    Report errors if the latex part is not found or is empty.
    """
    list_of_tag_pairs = get_list_of_tag_pairs_for_section(section)
    for tag_pair in list_of_tag_pairs:
        try:
            latex_content = extract_text_between_tags(response, *tag_pair)
        except ValueError:
            pass
        else:
            if latex_content == '':
                raise FailedToExtractLatexContent(f'The provided {section} is empty.')

            # TODO: we should try to format the latex and report formatting errors to chatgpt

            return tag_pair[0] + latex_content + (tag_pair[1] or '')

    raise FailedToExtractLatexContent(f'Failed to extract {section} from response. '
                                      f'The response does not contain: {list_of_tag_pairs[0]}.')
