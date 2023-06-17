from dataclasses import dataclass, field
from typing import Optional, List

from data_to_paper.env import SAVE_INTERMEDIATE_LATEX

from data_to_paper.utils.citataion_utils import remove_citations_from_section
from data_to_paper.utils import dedent_triple_quote_str
from data_to_paper.utils.nice_list import NiceList
from data_to_paper.utils.text_formatting import wrap_text_with_triple_quotes
from data_to_paper.utils.file_utils import get_non_existing_file_name

from data_to_paper.latex import FailedToExtractLatexContent, extract_latex_section_from_response
from data_to_paper.latex.exceptions import LatexCompilationError, UnwantedCommandsUsedInLatex
from data_to_paper.latex.latex_to_pdf import check_latex_compilation, remove_figure_envs_from_latex, \
    replace_special_chars, check_usage_of_unwanted_commands
from data_to_paper.latex.latex_section_tags import get_list_of_tag_pairs_for_section_or_fragment

from .base_products_conversers import ReviewBackgroundProductsConverser
from .result_converser import Rewind, NoResponse


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

        Please {goal_verb} the {goal_noun} again with this error corrected.
        """)
    rewind_after_getting_a_valid_response: Optional[Rewind] = Rewind.REPOST_AS_FRESH

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
        for section_name in self.section_names:
            latex = self._extract_latex_section_from_response(response, section_name)
            response = response.replace(latex, wrap_text_with_triple_quotes(latex, 'latex'))
        return super()._alter_self_response(response)

    def _get_fresh_looking_response(self, response) -> str:
        """
        Return a response that looks fresh.
        """
        if isinstance(self.returned_result, NoResponse):
            return super()._get_fresh_looking_response(response)
        return super()._get_fresh_looking_response('\n\n'.join(self.returned_result))

    def _get_latex_section_from_response(self, response: str, section_name: str) -> str:
        section = self._extract_latex_section_from_response(response, section_name)
        section = self._refine_extracted_section(section)
        return section

    def _extract_latex_section_from_response(self, response: str, section_name: str) -> str:
        """
        Extract a section from the response.
        """
        try:
            return extract_latex_section_from_response(response, section_name)
        except FailedToExtractLatexContent as e:
            tags_list = get_list_of_tag_pairs_for_section_or_fragment(section_name)
            tags = tags_list[0]
            self._raise_self_response_error(
                str(e),
                bump_model=len(tags_list) == 1 and tags[0] in response and tags[1] not in response
            )

    def _refine_extracted_section(self, extracted_section: str) -> str:
        if self.should_remove_citations_from_section:
            extracted_section = remove_citations_from_section(extracted_section)
        extracted_section = remove_figure_envs_from_latex(extracted_section)
        extracted_section = replace_special_chars(extracted_section)
        return extracted_section

    def _check_section(self, extracted_section: str, section_name: str):
        if SAVE_INTERMEDIATE_LATEX:
            file_stem = f'{self.conversation_name}__{section_name}'
            file_path = get_non_existing_file_name(self.output_directory / f'{file_stem}.pdf')
            file_stem, output_directory = file_path.stem, file_path.parent
        else:
            file_stem, output_directory = 'test', None
        try:
            check_latex_compilation(extracted_section, file_stem, output_directory)
        except LatexCompilationError as e:
            self._raise_self_response_error(str(e))
        try:
            check_usage_of_unwanted_commands(extracted_section)
        except UnwantedCommandsUsedInLatex as e:
            self._raise_self_response_error(str(e))

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

        for section_name, section in zip(self.section_names, section_contents):
            self._check_section(section, section_name)
