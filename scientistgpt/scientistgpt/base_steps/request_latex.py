from dataclasses import dataclass, field
from typing import Optional, Union, List

from scientistgpt.latex import FailedToExtractLatexContent, extract_latex_section_from_response
from scientistgpt.utils.citataion_utils import remove_citations_from_section
from scientistgpt.utils import dedent_triple_quote_str
from scientistgpt.utils.nice_list import NiceList
from scientistgpt.latex.exceptions import LatexCompilationError
from scientistgpt.latex.latex_to_pdf import test_latex_compilation, remove_figure_envs_from_latex, replace_special_chars

from .base_products_conversers import BaseProductsReviewGPT


@dataclass
class BaseLatexProductsReviewGPT(BaseProductsReviewGPT):
    """
    A base class for agents requesting chatgpt to write one or more latex sections.
    Option for removing citations from the section.
    Option for reviewing the sections (set max_review_turns > 0).
    """
    ADDITIONAL_DICT_ATTRS = BaseProductsReviewGPT.ADDITIONAL_DICT_ATTRS | {'section_name', 'pretty_section_names'}
    should_remove_citations_from_section = True

    section_names: List[str] = field(default_factory=list)

    # outputs:
    section_contents: List[str] = field(default_factory=list)

    @property
    def section_name(self) -> Optional[str]:
        if len(self.section_names) == 1:
            return self.section_names[0]
        return None

    @property
    def pretty_section_names(self) -> NiceList[str]:
        """
        Return the section names capitalized.
        """
        return NiceList((section_name.title() for section_name in self.section_names),
                        separator=', ', last_separator=' and ')

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
                extracted_section = remove_figure_envs_from_latex(extracted_section)
                extracted_section = replace_special_chars(extracted_section)
                test_latex_compilation(extracted_section)
                self.section_contents.append(extracted_section)
        except (FailedToExtractLatexContent, LatexCompilationError) as e:
            error_message = dedent_triple_quote_str("""
                {}

                Please rewrite the {} part again with the correct latex formatting.
                """).format(e, self.goal_noun)
            return error_message
        return None

    def get_sections(self) -> Union[str, list[str]]:
        self.initialize_and_run_dialog()
        return self.section_contents

    def get_section(self):
        return self.get_sections()[0]
