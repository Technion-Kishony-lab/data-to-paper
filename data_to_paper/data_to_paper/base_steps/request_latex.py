import re
from dataclasses import dataclass, field
from typing import Optional, List, Tuple

from data_to_paper.env import SAVE_INTERMEDIATE_LATEX

from data_to_paper.utils import dedent_triple_quote_str
from data_to_paper.utils.nice_list import NiceList
from data_to_paper.utils.text_formatting import wrap_text_with_triple_quotes
from data_to_paper.utils.file_utils import get_non_existing_file_name
from data_to_paper.latex import FailedToExtractLatexContent, extract_latex_section_from_response
from data_to_paper.latex.exceptions import UnwantedCommandsUsedInLatex, LatexProblemInCompilation, TooWideTableOrText
from data_to_paper.run_gpt_code.code_utils import extract_content_of_triple_quote_block, FailedExtractingBlock, \
    IncompleteBlockFailedExtractingBlock
from data_to_paper.utils.citataion_utils import find_citation_ids
from data_to_paper.utils.types import ListBasedSet
from data_to_paper.latex.latex_to_pdf import check_latex_compilation
from data_to_paper.latex.clean_latex import process_non_math_parts, check_usage_of_un_allowed_commands
from data_to_paper.latex.latex_section_tags import get_list_of_tag_pairs_for_section_or_fragment, \
    SECTIONS_OR_FRAGMENTS_TO_TAG_PAIR_OPTIONS

from .base_products_conversers import ReviewBackgroundProductsConverser
from .result_converser import Rewind, NoResponse


def is_similar_bibtex_ids(incorrect_id: str, correct_id: str) -> bool:
    """
    Return whether the two bibtex ids are similar.
    """
    correct_id = correct_id.lower()
    incorrect_id = incorrect_id.lower()
    return correct_id.startswith(incorrect_id) or incorrect_id.startswith(correct_id)


def replace_word(text, original_word, new_word):
    pattern = r'\b' + re.escape(original_word) + r'\b'
    return re.sub(pattern, new_word, text)


def remove_citations_from_section(section: str) -> str:
    r"""
    Return the section without citations (e.g. \cite{...}).
    """
    return re.sub(pattern=r'\s*\\cite[tp]?(\[.*?])?(\[.*?])?\{[^}]*}(?=\s*\.)?', repl='', string=section)


@dataclass
class LatexReviewBackgroundProductsConverser(ReviewBackgroundProductsConverser):
    """
    A base class for agents requesting chatgpt to write one or more latex sections.
    Option for removing citations from the section.
    Option for reviewing the sections (set max_review_turns > 0).
    """
    should_remove_citations_from_section: bool = True

    tolerance_for_too_wide_in_pts: Optional[float] = None  # If None, do not raise on too wide.

    section_names: List[str] = field(default_factory=list)

    response_to_self_error: str = dedent_triple_quote_str("""
        {}

        Please {goal_verb} the {goal_noun} again with this error corrected.
        """)
    rewind_after_getting_a_valid_response: Optional[Rewind] = Rewind.REPOST_AS_FRESH

    request_triple_quote_block: Optional[str] = None  # `None` or "" - do not request triple-quoted.
    # or, can be something like: 'Please send your response as a triple-backtick "latex" block.'

    un_allowed_commands: Tuple[str, ...] = (r'\cite', r'\verb', r'\begin{figure}')

    response_to_non_matching_citations: str = dedent_triple_quote_str("""
        The following citation ids were not found: 
        {}
        Please make sure all citation ids are writen exactly as in the citation lists above.
        """)

    response_to_floating_citations: str = dedent_triple_quote_str("""
        The following citation ids are not properly enclosed in \\cite{{}} command: 
        {}
        Please make sure all citation ids are enclosed in a \\cite{{}} command.
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

    def _get_fresh_looking_response(self, response) -> str:
        """
        Return a response that looks fresh.
        """
        if not isinstance(self.returned_result, NoResponse):
            response = '\n\n'.join(self.returned_result)
            if self.request_triple_quote_block:
                response = wrap_text_with_triple_quotes(response, 'latex')
        return super()._get_fresh_looking_response(response)

    def _get_allowed_bibtex_citation_ids(self) -> List[str]:
        r"""
        Return the bibtex citation ids that are allowed citing with \cite{}.
        """
        return []

    def _extract_latex_section_from_response(self, response: str, section_name: str) -> str:
        """
        Extract a section from the response.
        """
        if self.request_triple_quote_block:
            try:
                response = extract_content_of_triple_quote_block(response, 'latex', 'latex')
            except FailedExtractingBlock as e:
                self._raise_self_response_error(str(e), bump_model=isinstance(e, IncompleteBlockFailedExtractingBlock))
        try:
            return extract_latex_section_from_response(response, section_name)
        except FailedToExtractLatexContent as e:
            tags_list = get_list_of_tag_pairs_for_section_or_fragment(section_name)
            tags = tags_list[0]
            self._raise_self_response_error(
                str(e),
                bump_model=len(tags_list) == 1 and tags[0] in response and tags[1] not in response
            )

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

    def _process_non_math_parts(self, section: str) -> str:
        return process_non_math_parts(section)

    def _check_usage_of_un_allowed_commands(self, section: str) -> str:
        try:
            check_usage_of_un_allowed_commands(section, self.un_allowed_commands)
        except UnwantedCommandsUsedInLatex as e:
            self._raise_self_response_error(str(e))
        return section

    def _remove_citations_from_section(self, section) -> str:
        """
        Remove the citations that ChatGPT inserted by mistake.
        """
        if not self.should_remove_citations_from_section:
            return section
        section = remove_citations_from_section(section)
        # also remove \bibliographystyle{} and \bibliography{} commands
        section = re.sub(pattern=r'\s*\\bibliographystyle\{.*?\}', repl='', string=section)
        section = re.sub(pattern=r'\s*\\bibliography\{.*?\}', repl='', string=section)
        return section

    def _check_and_correct_citations(self, section: str) -> str:
        """
        Check that all \\cite{} commands refer to bibtex citations that are allowed.
        Raise if citing un-allowed citations, or correct similar citations to the correct one.
        """
        allowed_ids = self._get_allowed_bibtex_citation_ids()
        not_found_ids = ListBasedSet([citation_id for citation_id in find_citation_ids(section)
                                      if citation_id not in allowed_ids])
        # Correct almost-matching citations:
        not_found_and_not_corrected_ids = []
        for not_found_id in not_found_ids:
            similar_ids = [allowed_id for allowed_id in allowed_ids if is_similar_bibtex_ids(not_found_id, allowed_id)]
            if len(similar_ids) == 1:
                section = replace_word(section, not_found_id, similar_ids[0])
                self.comment(f'Replacing citation id {not_found_id} with {similar_ids[0]}', as_action=False)
            else:
                not_found_and_not_corrected_ids.append(not_found_id)
        if not_found_and_not_corrected_ids:
            self._raise_self_response_error(
                self.response_to_non_matching_citations.format(not_found_and_not_corrected_ids))
        return section

    def _check_for_floating_citations(self, section: str) -> str:
        r"""
        Check that there are no floating citations, not enclosed with \cite{}.
        """
        if self.response_to_floating_citations:
            section_without_citations = remove_citations_from_section(section)
            allowed_ids = self._get_allowed_bibtex_citation_ids()
            floating_ids = ListBasedSet([citation_id for citation_id in allowed_ids
                                         if citation_id in section_without_citations])
            if floating_ids:
                self._raise_self_response_error(self.response_to_floating_citations.format(floating_ids))
        return section

    def _process_citations(self, section: str) -> str:
        section = self._remove_citations_from_section(section)
        section = self._check_and_correct_citations(section)
        section = self._check_for_floating_citations(section)
        return section

    def _check_and_refine_section(self, section: str, section_name: str) -> str:
        section = self._check_usage_of_un_allowed_commands(section)
        section = self._process_citations(section)
        section = self._process_non_math_parts(section)
        return section

    def _check_no_additional_sections(self, response: str):
        """
        Check that there are no additional sections in the response.
        """
        num_sections = response.count('\\section')
        if num_sections > len([section_name for section_name in self.section_names
                               if section_name not in SECTIONS_OR_FRAGMENTS_TO_TAG_PAIR_OPTIONS]):
            self._raise_self_response_error(
                f'You must only write the {self.pretty_section_names} section.'
            )

    def _check_and_extract_result_from_self_response(self, response: str):
        """
        Check the response and extract latex sections from it into returned_result.
        Raise if there are errors that require self to revise the response.
        """

        self._check_no_additional_sections(response)

        # extract the latex sections
        section_contents = [self._extract_latex_section_from_response(response, section_name)
                            for section_name in self.section_names]

        # check and refine the sections
        for i in range(len(section_contents)):
            section_contents[i] = self._check_and_refine_section(section_contents[i], self.section_names[i])

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
