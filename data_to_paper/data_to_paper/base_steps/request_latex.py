from dataclasses import dataclass, field
from typing import Optional, List

from data_to_paper.env import SAVE_INTERMEDIATE_LATEX

from data_to_paper.utils.citataion_utils import remove_citations_from_section
from data_to_paper.utils import dedent_triple_quote_str
from data_to_paper.utils.nice_list import NiceList
from data_to_paper.utils.text_formatting import wrap_text_with_triple_quotes
from data_to_paper.utils.file_utils import get_non_existing_file_name

from data_to_paper.latex import FailedToExtractLatexContent, extract_latex_section_from_response
from data_to_paper.latex.exceptions import UnwantedCommandsUsedInLatex, LatexProblemInCompilation, NonLatexCitations, \
    TooWideTableOrText

from data_to_paper.latex.latex_to_pdf import check_latex_compilation, remove_figure_envs_from_latex, \
    replace_special_chars, check_usage_of_unwanted_commands, check_non_latex_citations
from data_to_paper.latex.latex_section_tags import get_list_of_tag_pairs_for_section_or_fragment, \
    SECTIONS_OR_FRAGMENTS_TO_TAG_PAIR_OPTIONS

from .base_products_conversers import ReviewBackgroundProductsConverser
from .result_converser import Rewind, NoResponse
from ..run_gpt_code.code_utils import extract_content_of_triple_quote_block, FailedExtractingBlock


@dataclass
class LatexReviewBackgroundProductsConverser(ReviewBackgroundProductsConverser):
    """
    A base class for agents requesting chatgpt to write one or more latex sections.
    Option for removing citations from the section.
    Option for reviewing the sections (set max_review_turns > 0).
    """
    should_remove_citations_from_section = True

    tolerance_for_too_wide_in_pts: Optional[float] = None  # If None, do not raise on too wide.

    section_names: List[str] = field(default_factory=list)

    response_to_self_error: str = dedent_triple_quote_str("""
        {}

        Please {goal_verb} the {goal_noun} again with this error corrected.
        """)
    rewind_after_getting_a_valid_response: Optional[Rewind] = Rewind.REPOST_AS_FRESH

    request_triple_quote_block: Optional[str] = None  # `None` or "" - do not request triple-quoted.
    # or, can be something like: 'Please send your response as a triple-backtick "latex" block.'

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

    def _get_fresh_looking_response(self, response) -> str:
        """
        Return a response that looks fresh.
        """
        if isinstance(self.returned_result, NoResponse):
            return super()._get_fresh_looking_response(response)
        response = '\n\n'.join(self.returned_result)
        if self.request_triple_quote_block:
            response = wrap_text_with_triple_quotes(response, 'latex')
        return super()._get_fresh_looking_response(response)

    def _get_latex_section_from_response(self, response: str, section_name: str) -> str:
        if self.request_triple_quote_block:
            response = self._extract_triply_quoted_latex_from_response(response)
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

    def _check_latex_compilation(self, section: str, section_name: str) -> Optional[LatexProblemInCompilation]:
        if SAVE_INTERMEDIATE_LATEX:
            file_stem = f'{section_name}__{self.conversation_name}'
            file_path = get_non_existing_file_name(self.output_directory / f'{file_stem}.pdf')
            file_stem, output_directory = file_path.stem, file_path.parent
        else:
            file_stem, output_directory = 'test', None
        try:
            check_latex_compilation(section, file_stem, output_directory, self.tolerance_for_too_wide_in_pts)
        except LatexProblemInCompilation as e:
            return e

    def _check_section(self, extracted_section: str, section_name: str):
        self._check_usage_of_unwanted_commands(extracted_section)
        self._check_usage_of_non_latex_citations(extracted_section)

    def _check_usage_of_unwanted_commands(self, extracted_section: str, unwanted_commands: List[str] = None):
        try:
            check_usage_of_unwanted_commands(extracted_section, unwanted_commands)
        except UnwantedCommandsUsedInLatex as e:
            self._raise_self_response_error(str(e))

    def _check_usage_of_non_latex_citations(self, extracted_section: str):
        """
        Check that there are no citations that are not in latex format.
        """
        try:
            check_non_latex_citations(extracted_section)
        except NonLatexCitations as e:
            self._raise_self_response_error(str(e))

    def _check_no_additional_sections(self, response: str):
        """
        Check that there are no additional sections in the response.
        """
        num_sections = response.count('\\section')
        if num_sections != len([section_name for section_name in self.section_names
                                if section_name not in SECTIONS_OR_FRAGMENTS_TO_TAG_PAIR_OPTIONS]):
            self._raise_self_response_error(
                f'You must only write the {self.pretty_section_names} section.'
            )

    def _extract_triply_quoted_latex_from_response(self, response: str) -> str:
        """
        Extract latex sections from the response.
        """
        try:
            return extract_content_of_triple_quote_block(response, 'latex', 'latex')
        except FailedExtractingBlock as e:
            self._raise_self_response_error(str(e))

    def _check_and_extract_result_from_self_response(self, response: str):
        """
        Check the response and extract latex sections from it into returned_result.
        Raise if there are errors that require self to revise the response.
        """

        self._check_no_additional_sections(response)

        # extract the latex sections
        section_contents = [self._get_latex_section_from_response(response, section_name)
                            for section_name in self.section_names]

        # check the latex compilation
        exceptions = [self._check_latex_compilation(section, section_name)
                      for section, section_name in zip(section_contents, self.section_names)]
        exceptions = [e for e in exceptions if e is not None]

        # store the result if there are no exceptions, forgiving TooWideTableOrText:
        is_just_too_wide = [isinstance(e, TooWideTableOrText) for e in exceptions]
        if all(is_just_too_wide):
            self.returned_result = section_contents

        # raise the compilation errors
        if any(exceptions):
            self._raise_self_response_error('\n\n'.join((str(e) for e in exceptions)))

        # check the sections for other problems
        for section_name, section in zip(self.section_names, section_contents):
            self._check_section(section, section_name)
