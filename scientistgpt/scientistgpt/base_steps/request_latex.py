from dataclasses import dataclass, field
from typing import Optional, List

from scientistgpt.utils.citataion_utils import remove_citations_from_section
from scientistgpt.utils import dedent_triple_quote_str
from scientistgpt.utils.nice_list import NiceList
from scientistgpt.utils.text_formatting import wrap_text_with_triple_quotes

from scientistgpt.latex import FailedToExtractLatexContent, extract_latex_section_from_response
from scientistgpt.latex.exceptions import LatexCompilationError, UnwantedCommandsUsedInLatex
from scientistgpt.latex.latex_to_pdf import check_latex_compilation, remove_figure_envs_from_latex, \
    replace_special_chars, check_usage_of_unwanted_commands

from .base_products_conversers import ReviewBackgroundProductsConverser


@dataclass
class LatexReviewBackgroundProductsConverser(ReviewBackgroundProductsConverser):
    """
    A base class for agents requesting chatgpt to write one or more latex sections.
    Option for removing citations from the section.
    Option for reviewing the sections (set max_review_turns > 0).
    """
    should_remove_citations_from_section = True

    section_names: List[str] = field(default_factory=list)

    response_to_self_error: str = dedent_triple_quote_str("""
        {}

        Please {goal_verb} the {goal_noun} part again with the correct latex formatting.
        """)

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

    def _alter_self_response(self, response: str) -> str:
        return super()._alter_self_response(wrap_text_with_triple_quotes(response, 'latex'))

    def _get_latex_section_from_response(self, response: str, section_name: str) -> str:
        section = self._extract_latex_section_from_response(response, section_name)
        section = self._refine_extracted_section(section)
        section = self._check_section(section)
        return section

    def _extract_latex_section_from_response(self, response: str, section_name: str) -> str:
        """
        Extract a section from the response.
        """
        try:
            return extract_latex_section_from_response(response, section_name)
        except FailedToExtractLatexContent as e:
            self._raise_self_response_error(str(e))

    def _refine_extracted_section(self, extracted_section: str) -> str:
        if self.should_remove_citations_from_section:
            extracted_section = remove_citations_from_section(extracted_section)
        extracted_section = remove_figure_envs_from_latex(extracted_section)
        extracted_section = replace_special_chars(extracted_section)
        return extracted_section

    def _check_section(self, extracted_section: str) -> str:
        try:
            check_latex_compilation(extracted_section)
        except LatexCompilationError as e:
            self._raise_self_response_error(str(e))
        try:
            check_usage_of_unwanted_commands(extracted_section)
        except UnwantedCommandsUsedInLatex as e:
            self._raise_self_response_error(str(e))
        return extracted_section

    def _check_and_extract_result_from_self_response(self, response: str):
        """
        Check the response and extract latex sections from it into returned_result.
        If the there are errors that require self to revise the response, raise an SelfResponseError describing
        the problem.
        """
        section_contents = []
        for section_name in self.section_names:
            section_contents.append(self._get_latex_section_from_response(response, section_name))
        self.returned_result = section_contents
