import re
from dataclasses import dataclass, field

from typing import Optional, List, Tuple

from data_to_paper.env import WRITING_MODEL_ENGINE

from data_to_paper.text import dedent_triple_quote_str, wrap_as_block
from data_to_paper.utils.nice_list import NiceList
from data_to_paper.latex import FailedToExtractLatexContent, extract_latex_section_from_response
from data_to_paper.latex.exceptions import UnwantedCommandsUsedInLatex, BaseLatexProblemInCompilation
from data_to_paper.run_gpt_code.code_utils import extract_content_of_triple_quote_block, FailedExtractingBlock, \
    IncompleteBlockFailedExtractingBlock, NoBlocksFailedExtractingBlock
from data_to_paper.latex.citataion_utils import find_citation_ids
from data_to_paper.utils.types import ListBasedSet
from data_to_paper.latex.latex_doc import LatexDocument
from data_to_paper.latex.clean_latex import process_latex_text_and_math, check_usage_of_un_allowed_commands
from data_to_paper.latex.latex_section_tags import get_list_of_tag_pairs_for_section_or_fragment, \
    SECTIONS_OR_FRAGMENTS_TO_TAG_PAIR_OPTIONS
from data_to_paper.servers.model_engine import ModelEngine

from .base_products_conversers import ReviewBackgroundProductsConverser
from .result_converser import Rewind


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
    A base class for agents requesting the LLM to write one or more latex sections.
    Option for removing citations from the section.
    Option for reviewing the sections (set max_review_turns > 0).
    """
    latex_document: LatexDocument = field(default_factory=LatexDocument)
    model_engine: ModelEngine = WRITING_MODEL_ENGINE
    should_remove_citations_from_section: bool = True

    section_names: List[str] = field(default_factory=list)

    your_response_should_be_formatted_as: str = "a triple backtick latex block."
    formatting_instructions_for_feedback: str = dedent_triple_quote_str("""
        Please {goal_verb} the {goal_noun} again according to my feedback above.

        Remember, your response should be formatted as {your_response_should_be_formatted_as}
        """)
    rewind_after_getting_a_valid_response: Optional[Rewind] = Rewind.AS_FRESH

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
                        separator=', ', last_separator=' and ', wrap_with="`")

    def get_valid_result_as_markdown(self) -> str:
        return wrap_as_block('\n\n'.join(self.valid_result), 'latex')

    def _convert_extracted_text_to_fresh_looking_response(self, extracted_text: List[str]) -> str:
        """
        Return a response that looks fresh.
        """
        s = super()._convert_extracted_text_to_fresh_looking_response(extracted_text)
        s = wrap_as_block(s, 'latex')
        return s

    def _convert_valid_result_back_to_extracted_text(self, valid_result: List[str]) -> List[str]:
        return valid_result

    def _get_allowed_bibtex_citation_ids(self) -> List[str]:
        r"""
        Return the bibtex citation ids that are allowed citing with \cite{}.
        """
        return []

    def _extract_latex_section_from_response(self, response: str, section_name: str) -> str:
        """
        Extract a section from the response.
        """
        tags_list = get_list_of_tag_pairs_for_section_or_fragment(section_name)
        tags = tags_list[0]
        is_flanking_tags = len(tags_list) == 1 and tags.is_flanking()
        try:
            response = extract_content_of_triple_quote_block(response, 'latex', 'latex')
        except FailedExtractingBlock as e:
            if isinstance(e, NoBlocksFailedExtractingBlock) and is_flanking_tags:
                pass
            else:
                self._raise_self_response_error(
                    title='# Failed to extract latex block',
                    error_message=str(e),
                    missing_end=isinstance(e, IncompleteBlockFailedExtractingBlock))
        try:
            return extract_latex_section_from_response(response, section_name)
        except FailedToExtractLatexContent as e:
            self._raise_self_response_error(
                title='# Failed to extract latex section(s)',
                error_message=str(e),
                missing_end=is_flanking_tags and tags[0] in response and tags[1] not in response)

    def _process_non_math_parts(self, section: str) -> str:
        return process_latex_text_and_math(section)

    def _check_usage_of_un_allowed_commands(self, section: str) -> str:
        try:
            check_usage_of_un_allowed_commands(section, self.un_allowed_commands)
        except UnwantedCommandsUsedInLatex as e:
            self._raise_self_response_error(
                title='# Unwanted commands used in latex',
                error_message=str(e))
        return section

    def _remove_citations_from_section(self, section) -> str:
        """
        Remove the citations that the LLM inserted by mistake.
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
                title='# Citation ids not found',
                error_message=self.response_to_non_matching_citations.format(not_found_and_not_corrected_ids))
        return section

    def _check_for_floating_citations(self, section: str) -> str:
        r"""
        Check that there are no floating citations, namely citations not enclosed with \cite{}.
        """
        if self.response_to_floating_citations:
            section_without_citations = remove_citations_from_section(section)
            allowed_ids = self._get_allowed_bibtex_citation_ids()
            floating_ids = ListBasedSet([citation_id for citation_id in allowed_ids
                                         if citation_id in section_without_citations])
            if floating_ids:
                self._raise_self_response_error(
                    title='# Floating citation ids',
                    error_message=self.response_to_floating_citations.format(floating_ids))
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
        required_sections = [section_name.title() for section_name in self.section_names
                             if section_name not in SECTIONS_OR_FRAGMENTS_TO_TAG_PAIR_OPTIONS]
        provided_sections = re.findall(pattern=r'\\section\*?\{([^}]*)\}', string=response)
        provided_but_not_required_sections = set(provided_sections) - set(required_sections)
        if provided_but_not_required_sections:
            self._raise_self_response_error(
                title='# Undesired sections in the response',
                error_message=dedent_triple_quote_str(f"""
                You must only write the {self.pretty_section_names} section(s).
                But, you wrote also these section(s):
                {NiceList(provided_but_not_required_sections, wrap_with="`")}
                """)
            )

        # check for duplicates in provided_sections:
        sections_appearing_more_than_once = [section for section in provided_sections
                                             if provided_sections.count(section) > 1]
        if sections_appearing_more_than_once:
            self._raise_self_response_error(
                title='# Duplicate sections in the response',
                error_message=dedent_triple_quote_str(f"""
                You wrote the following section(s) more than once:
                {NiceList(sections_appearing_more_than_once, wrap_with="`")}
                """)
            )

    def _check_response_and_get_extracted_text(self, response: str) -> List[str]:
        """
        Check the response from self and extract the needed information into extracted_text.
        """
        self._check_no_additional_sections(response)
        return [self._extract_latex_section_from_response(response, section_name)
                for section_name in self.section_names]

    def _check_extracted_text_and_update_valid_result(self, extracted_text: List[str]):

        # check and refine the sections
        for i in range(len(extracted_text)):
            extracted_text[i] = self._check_and_refine_section(extracted_text[i], self.section_names[i])

        # check the latex compilation
        try:
            _, _, width = self.latex_document.compile_document(
                {section_name: section for section_name, section in zip(self.section_names, extracted_text)})
        except BaseLatexProblemInCompilation as e:
            self._raise_self_response_error(
                title='# LaTex compilation error',
                error_message=str(e))

        # store the result if there are no exceptions:
        self._update_valid_result(extracted_text)
