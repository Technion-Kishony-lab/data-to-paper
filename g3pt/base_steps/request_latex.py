from dataclasses import dataclass, field
from typing import Optional, Union, List

from g3pt.latex import FailedToExtractLatexContent, extract_latex_section_from_response
from g3pt.utils.citataion_utils import remove_citations_from_section
from g3pt.utils import dedent_triple_quote_str
from g3pt.utils.replacer import with_attribute_replacement

from .base_products_conversers import BaseProductsReviewGPT


@dataclass
class BaseLatexProductsReviewGPT(BaseProductsReviewGPT):
    """
    A base class for agents requesting chatgpt to write one or more latex sections.
    Option for removing citations from the section.
    Option for reviewing the sections (set max_review_turns > 0).
    """

    should_remove_citations_from_section = True

    # outputs:
    section_contents: Union[str, List[str]] = field(default_factory=list)

    def _check_self_response(self, response: str) -> Optional[str]:
        """
        Check that the response is a valid latex section
        """
        try:
            self.section_contents = []
            for section_name in self.section_names:
                extracted_section = extract_latex_section_from_response(response, section_name)
                if self.should_remove_citations_from_section:
                    extracted_section = remove_citations_from_section(extracted_section)
                self.section_contents.append(extracted_section)
        except FailedToExtractLatexContent as e:
            error_message = dedent_triple_quote_str("""
                {}

                Please rewrite the {} part again with the correct latex formatting.
                """).format(e, self.goal_noun)
            return error_message
        return None

    @with_attribute_replacement
    def get_sections(self) -> Union[str, list[str]]:
        self.initialize_and_run_dialog()
        return self.section_contents
