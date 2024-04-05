from dataclasses import dataclass, field
from typing import Dict, Set, Tuple, List, Any, Optional

from data_to_paper.utils import dedent_triple_quote_str
from data_to_paper.utils.nice_list import NiceList
from data_to_paper.utils.types import ListBasedSet

from data_to_paper.servers.crossref import CROSSREF_SERVER_CALLER, CrossrefCitation, ServerErrorCitationException
from data_to_paper.base_steps.request_python_value import PythonValueReviewBackgroundProductsConverser
from data_to_paper.base_steps.result_converser import Rewind

from .cast import ScientificAgent
from .scientific_products import ScientificProducts


@dataclass
class RewriteSentenceWithCitations(PythonValueReviewBackgroundProductsConverser):
    """
    Given a sentence and a list of citations, choose the ones that match the sentence and
    rewrite the sentence with the citations.
    This class is called on already initialized conversation.
    """

    rewind_after_getting_a_valid_response: Optional[Rewind] = Rewind.ACCUMULATE
    rewind_after_end_of_review: Optional[Rewind] = Rewind.DELETE_ALL

    assistant_agent: ScientificAgent = ScientificAgent.Performer
    user_agent: ScientificAgent = ScientificAgent.CitationExpert

    goal_noun: str = 'Choose citations for a given sentence'
    goal_verb: str = 'find'

    value_type: type = List[str]
    max_reviewing_rounds: int = 0  # no review
    fake_performer_request_for_help: str = None
    fake_reviewer_agree_to_help: str = None
    fake_performer_message_to_add_after_max_rounds: str = None
    max_valid_response_iterations: int = 2
    mission_prompt: str = dedent_triple_quote_str("""
        Choose the most appropriate citations to add for the sentence: 

        "{sentence}"

        Choose as many relevant citations as possible from the following citations:

        {citations}

        Send your reply formatted as a Python list of str, representing the ids of the citations you choose. 
        For example, write:
        ```python
        ["AuthorX2022", "AuthorY2009"]
        ```

        where AuthorX2022 and AuthorY2009 are the ids of the citations you think are making a good fit for the sentence.
        Choose only citations that are relevant to the sentence.
        You can choose one or more citations, or you can choose not adding citations to this sentence by replying `[]`.
        """)

    response_to_self_error = dedent_triple_quote_str("""
        {}
        Please try again making sure you return the chosen citations with the correct format, like this:
        ``` 
        ["AuthorX2022Title", "AuthorY2009Title"]
        ```
        """)

    sentence: str = None
    citations: List[CrossrefCitation] = field(default_factory=list)
    chosen_citation_ids: Set[str] = field(default_factory=set)

    @property
    def citation_ids(self) -> List[str]:
        return [citation.bibtex_id for citation in self.citations]

    def _check_response_value(self, response_value: Any) -> Any:
        # we declare the result as "valid" even if we can't find any citations:
        self._update_valid_result(None)
        ids_not_in_options = self._add_citations_in_options_and_return_citations_not_in_options(response_value)
        if len(ids_not_in_options) > 0:
            self._raise_self_response_error(
                f'You returned {ids_not_in_options}, which is not part of the allowed options: {self.citation_ids}.')
        return None  # this will get into the response_value, which we are not using.

    def _add_citations_in_options_and_return_citations_not_in_options(self, chosen_citation_ids: List[str]) -> Set[str]:
        """
        Validate that the response is in the correct format and all ids are existing ones.
        """
        not_in_citations = ListBasedSet()
        for citation_id in chosen_citation_ids:
            if citation_id in self.citation_ids:
                self.chosen_citation_ids.add(citation_id)
            else:
                not_in_citations.add(citation_id)
        return not_in_citations

    def get_rewritten_sentence(self):
        """
        Add the chosen citations at the end of the sentence.
        """
        if len(self.chosen_citation_ids) == 0:
            return self.sentence
        return self.sentence.rstrip('.') + ' ' + '\\cite{' + ', '.join(self.chosen_citation_ids) + '}.'

    def get_rewritten_sentence_and_chosen_citations(self) -> Tuple[str, Set[CrossrefCitation]]:
        self.initialize_and_run_dialog()
        return (self.get_rewritten_sentence(),
                {citation for citation in self.citations if citation.bibtex_id in self.chosen_citation_ids})


@dataclass
class AddCitationReviewGPT(PythonValueReviewBackgroundProductsConverser):
    """
    Given a section of a paper, add citations to the factual sentences in the section.
    """

    rewind_after_getting_a_valid_response: Optional[Rewind] = Rewind.ACCUMULATE
    rewind_after_end_of_review: Optional[Rewind] = Rewind.DELETE_ALL

    value_type: type = Dict[str, str]
    products: ScientificProducts = None
    # in the actual call to add_background, we will be adding to the background also the specific section
    # see self.actual_background_product_fields

    background_product_fields: Tuple[str, ...] = ()
    conversation_name: str = 'add_citations_{section_name}'
    assistant_agent: ScientificAgent = ScientificAgent.Performer
    user_agent: ScientificAgent = ScientificAgent.CitationExpert
    max_reviewing_rounds: int = 0  # 0 no review
    max_valid_response_iterations: int = 2
    goal_verb: str = 'add citations to'
    goal_noun: str = '{section_name} section of the paper'

    # override the default system prompt:
    system_prompt: str = dedent_triple_quote_str("""
        You are a scientific citation expert. 
    """)

    mission_prompt: str = dedent_triple_quote_str("""
        Extract from the above section of a scientific paper all the factual sentences to which we need to \t
        add citations.

        Return a Python Dict[str, str] mapping each chosen sentence to a short literature search query \t
        (up to a maximum of 5 words), like this:

        ```python
        {
         "This is a sentence that needs to have references": "Query for searching citations for this sentence", 
         "This is another important claim": "Some important keywords for this sentence", 
         "This is the another factual sentence that needs a source": "This is the best query for this sentence",
        }
        ```

        Identify *all* the sentences that you think we need to add citations to - you should include any sentence 
        that can benefit from a reference.

        However, be cautious to avoid choosing sentences that do not refer to existing knowledge, but rather \t
        describe the finding of the current paper.
    """)

    response_to_self_error: str = dedent_triple_quote_str("""
        {}
        Please try again making sure you return the results with the correct format, like this:
        ```python
        {"sentence extracted from the section": "query of the key sentence", 
        "another sentence extracted from the section": "the query of this sentence"}
        ```
    """)

    fake_performer_message_to_add_after_max_rounds: str = None

    # input:
    section_name: str = None  # The section of the paper to which we are adding citations to.

    # output:
    max_number_of_api_calls: int = 3
    current_sentence_citations_ids: Set[str] = field(default_factory=set)
    sentences_to_queries: Dict[str, str] = field(default_factory=dict)

    @property
    def section(self):
        return self.products.get_paper_sections_without_citations()[self.section_name]

    def _add_sentences_in_section_and_return_sentences_not_in_section(self, sentences_to_queries: Dict[str, str]
                                                                      ) -> List[str]:
        """
        For each sentence in sentences_to_queries, check if it is in the section. If it is, add it to
        self.sentences_to_queries. Return the sentences that are not in the section.
        """
        sentences_not_in_section = []
        for sentence, query in sentences_to_queries.items():
            if sentence in self.section:
                self.sentences_to_queries[sentence] = query
            else:
                sentences_not_in_section.append(sentence)
        return sentences_not_in_section

    def _find_citations_for_sentences(self, sentences_to_queries: Dict[str, str]) -> Dict[str, List[CrossrefCitation]]:
        """
        Find citations for the sentences in sentences_to_queries using their search queries.
        """
        sentences_to_citations = {}
        for sentence_number, (sentence, query) in enumerate(sentences_to_queries.items()):
            for number_of_tries in range(self.max_number_of_api_calls):
                try:
                    sentences_to_citations[sentence] = CROSSREF_SERVER_CALLER.get_server_response(query)
                    break
                except ServerErrorCitationException as e:
                    self.comment(f"CrossRef server error: {e}", web_conversation_name=None)
            else:
                self.apply_append_user_message(f"I failed finding citations for sentence #{sentence_number + 1}",
                                               ignore=True)
                continue
            self.apply_append_user_message(f"I found {len(sentences_to_citations[sentence])} citations "
                                           f"for sentence #{sentence_number + 1}", ignore=True)
        return sentences_to_citations

    @property
    def actual_background_product_fields(self) -> Tuple[str, ...]:
        return super().actual_background_product_fields + ('paper_sections:' + self.section_name, )

    def _check_response_value(self, response_value: Any) -> Any:
        """
        Check that the response dict contains only sentences that are in the section.
        Collect the sentences that are in the section.
        raise an error if there are sentences that are not in the section.
        """
        # we declare the result as "valid" even if we can't find any sentences:
        self._update_valid_result(None)
        sentences_not_in_section = self._add_sentences_in_section_and_return_sentences_not_in_section(response_value)
        if sentences_not_in_section:
            if len(sentences_not_in_section) == len(response_value):
                self._raise_self_response_error(
                    f'The sentences that you returned are not precise extraction from the section.')
            self._raise_self_response_error(
                f'The following sentences that you returned are not precise extraction from the section:\n'
                f'{sentences_not_in_section}.\n')
        return None  # this will get into the response_value, which we are not using.

    def rewrite_section_with_citations(self) -> Tuple[str, ListBasedSet[CrossrefCitation]]:
        """
        Rewrite the section with the citations.
        """
        self.initialize_and_run_dialog()
        # this runs the dialog and updates self.sentences_to_queries
        # we don't check if initialize_and_run_dialog() returns None, because even if it failed,
        # we might have accumulated some sentences through the process.

        sentences_to_citations = self._find_citations_for_sentences(self.sentences_to_queries)
        updated_section = self.section
        all_citations: ListBasedSet[CrossrefCitation] = ListBasedSet()
        for sentence, sentence_citations in sentences_to_citations.items():
            self.conversation_manager.reset_back_to_tag('after_background')
            if not sentence_citations:
                rewritten_sentence = sentence
                chosen_citations = ListBasedSet()
            else:
                rewritten_sentence, chosen_citations = \
                    RewriteSentenceWithCitations.from_(
                        self,
                        is_new_conversation=False,
                        sentence=sentence,
                        citations=NiceList(sentence_citations, separator='\n\n', last_separator=None),
                    ).get_rewritten_sentence_and_chosen_citations()
            updated_section = updated_section.replace(sentence, rewritten_sentence)
            all_citations |= chosen_citations
        nice_citations = NiceList(all_citations, separator='\n\n', last_separator=None)
        self.apply_append_user_message(
            f'Nice - you now have the {self.section_name.title()} with citations!\n\nHere it is\n\n'
            f'{updated_section}\n\n{nice_citations}', ignore=True)
        return updated_section, all_citations
