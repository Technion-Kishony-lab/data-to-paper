from dataclasses import dataclass, field
from typing import Dict, Set, Tuple, Optional, List, Any

from scientistgpt.utils import dedent_triple_quote_str
from scientistgpt.utils.replacer import with_attribute_replacement
from scientistgpt.utils.text_utils import NiceList

from scientistgpt.servers.crossref import CROSSREF_SERVER_CALLER, CrossrefCitation, ServerErrorCitationException
from scientistgpt.base_steps.request_python_value import BasePythonValueProductsReviewGPT

from .cast import ScientificAgent
from .scientific_products import ScientificProducts


@dataclass
class RewriteSentenceWithCitations(BasePythonValueProductsReviewGPT):
    """
    Given a sentence and a list of citations, choose the ones that match the sentence and
    rewrite the sentence with the citations.
    This class is called on already initialized conversation.
    """
    assistant_agent: ScientificAgent = ScientificAgent.Performer
    user_agent: ScientificAgent = ScientificAgent.CitationExpert

    goal_noun: str = 'Choose citations for a given sentence'
    goal_verb: str = 'find'

    value_type: type = List[str]
    max_reviewing_rounds: int = 0  # no review
    fake_performer_request_for_help: str = None
    fake_reviewer_agree_to_help: str = None
    fake_performer_message_to_add_after_max_rounds: str = None
    max_attempts_per_round: int = 2
    user_initiation_prompt: str = dedent_triple_quote_str("""
        Choose the most appropriate citations to add for the sentence: 

        "{sentence}"

        Choose as many relevant citations as possible from the following citations:

        {citations}

        Send your reply formatted as a Python list of str, representing the ids of the citations you choose. 
        For example, write: 
        `["AuthorX2022", "AuthorY2009"]`
        where AuthorX2022 and AuthorY2009 are the ids of the citations you think are making a good fit for the sentence.
        Choose only citations that are relevant to the sentence.
        You can choose one or more citations, or you can choose not adding citations to this sentence by replying `[]`.
        """)

    sentence_to_add_to_error_message_upon_failed_check_self_response = dedent_triple_quote_str("""
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
        return [citation.get_bibtex_id() for citation in self.citations]

    def _check_response_value(self, response_value: Any) -> Optional[str]:
        ids_not_in_options = \
            self._add_citations_in_options_and_return_citations_not_in_options(response_value)

        if len(ids_not_in_options) > 0:
            return \
                f'You returned citations that are not included in the provided citation options.' \
                f'Specifically, you returned {ids_not_in_options}, while the allowed options are: {self.citation_ids}.'
        return None

    def _add_citations_in_options_and_return_citations_not_in_options(self, chosen_citation_ids: List[str]) -> Set[str]:
        """
        Validate that the response is in the correct format and all ids are existing ones.
        """
        not_in_citations = set()
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
                {citation for citation in self.citations if citation.get_bibtex_id() in self.chosen_citation_ids})


@dataclass
class AddCitationReviewGPT(BasePythonValueProductsReviewGPT):
    """
    Given a section of a paper, add citations to the factual sentences in the section.
    """
    fake_performer_request_for_help: str = 'Hi, can you please help me with adding citations to my paper?'
    fake_reviewer_agree_to_help: str = 'Sure, I am happy to guide and help you with adding citations to your paper.\n' \
                                       'Please just provide some context first.'
    value_type: type = Dict[str, str]
    products: ScientificProducts = None
    # in the actual call to add_background, we will be adding to the background also the specific section
    # see _get_background_product_fields()
    background_product_fields = ['research_goal', 'results_summary', 'title_and_abstract']
    conversation_name: str = 'add_citations_{section_name}'
    assistant_agent: ScientificAgent = ScientificAgent.Performer
    user_agent: ScientificAgent = ScientificAgent.CitationExpert
    max_reviewing_rounds: int = 0  # 0 no review
    max_attempts_per_round: int = 2
    goal_noun: str = '{section_name} citations'

    # override the default system prompt:
    system_prompt: str = dedent_triple_quote_str(r"""
        You are a scientific citation expert. 
        You are given a section of a paper, and you need to follow the following steps:
        1. Choose factual sentences that need to be cited.
        2. Provided with list of possible citations, choose the most appropriate ones for each of the sentences. 
    """)

    user_initiation_prompt: str = dedent_triple_quote_str(r"""
        Extract from the above section as many relevant factual sentences as possible to which we need to add citations. 
        For each of the chosen sentences, create a short query for a citation search for this sentence.
        You need to return a dict mapping each sentence to its respective reference search query.
        Your response should be in the following format: 
        {{
         "This is a sentence that needs to have references": "Query for searching citations for this sentence", 
         "This is another important claim": "Some important keywords for this sentence", 
         "This is the another factual sentence that needs a source": "This is the best query for this sentence",
        }}
        This is of course just an example. 
        Identify *all* the sentences that you think we need to add citations to.

        Return only a dict of "sentence: query" pairs, without any other text.
    """)

    sentence_to_add_to_error_message_upon_failed_check_self_response: str = dedent_triple_quote_str("""
        Please try again making sure you return the results with the correct format, like this:
        ``` 
        {{"sentence extracted from the section": "query of the key sentence", 
        "another sentence extracted from the section": "the query of this sentence"}}
        ```
    """)

    # input:
    section_name: str = None  # The section of the paper to which we are adding citations to.

    # output:
    max_number_of_api_calls: int = 3
    current_sentence_citations_ids: Set[str] = field(default_factory=set)
    sentences_to_queries: Dict[str, str] = field(default_factory=dict)

    @property
    def section(self):
        return self.products.paper_sections[self.section_name]

    def _add_sentences_in_section_and_return_sentences_not_in_section(self, sentences_queries: Dict[str, str]
                                                                      ) -> List[str]:
        """
        For each sentence in sentences_to_queries, check if it is in the section. If it is, add it to
        self.sentences_to_queries. Return the sentences that are not in the section.
        """
        sentences_not_in_section = []
        for sentence, query in sentences_queries.items():
            if sentence in self.section:
                self.sentences_to_queries[sentence] = query
            else:
                sentences_not_in_section.append(sentence)
        return sentences_not_in_section

    def _find_citations_for_sentences(self) -> Dict[str, List[CrossrefCitation]]:
        """
        Find citations for the sentences in sentences_to_queries using their search queries.
        """
        sentences_to_citations = {}
        for sentence_number, (sentence, query) in enumerate(self.sentences_to_queries.items()):
            for number_of_tries in range(self.max_number_of_api_calls):
                message = f'Searching citations for sentence {sentence_number + 1}, try {number_of_tries + 1}... '
                try:
                    sentences_to_citations[sentence] = CROSSREF_SERVER_CALLER.get_server_response(query)
                    break
                except ServerErrorCitationException as e:
                    self.comment(message + f"CrossRef server error: {e}")
            else:
                self.comment(f"Could not find citations for the sentence:\n{sentence}.")
                continue
            self.comment(message + 'Successful!')

        return sentences_to_citations

    def _get_background_product_fields(self):
        return super()._get_background_product_fields() + ['paper_sections_' + self.section_name]

    def _check_response_value(self, response_value: Any) -> Optional[str]:
        """
        Check that the response value is valid.
        Return a feedback message if it is not valid, otherwise return None.
        """
        sentences_not_in_section = self._add_sentences_in_section_and_return_sentences_not_in_section(response_value)
        if sentences_not_in_section:
            if len(sentences_not_in_section) == len(response_value):
                return \
                    f'The sentences that you returned are not precise extraction from the section.'
            return \
                f'The following sentences that you returned are not precise extraction from the section:\n' \
                f'{sentences_not_in_section}.\n'
        return None

    @with_attribute_replacement
    def rewrite_section_with_citations(self) -> Tuple[str, Set[CrossrefCitation]]:
        """
        Rewrite the section with the citations.
        """
        self.initialize_and_run_dialog()
        # this tuns the dialog and updates self.sentences_to_queries
        # we don't check if initialize_and_run_dialog() returns None, because even if it failed,
        # we might have accumulated some sentences through the process.

        sentences_to_citations = self._find_citations_for_sentences()
        updated_section = self.section
        all_citations: Set[CrossrefCitation] = set()
        for sentence, sentence_citations in sentences_to_citations.items():
            self.conversation_manager.reset_back_to_tag('after_background')
            if not sentence_citations:
                rewritten_sentence = sentence
                chosen_citations = set()
            else:
                rewritten_sentence, chosen_citations = \
                    RewriteSentenceWithCitations.from_(
                        self,
                        sentence=sentence,
                        citations=NiceList(sentence_citations, separator='\n\n', last_separator=None),
                    ).get_rewritten_sentence_and_chosen_citations()
            updated_section = updated_section.replace(sentence, rewritten_sentence)
            all_citations |= chosen_citations
        return updated_section, all_citations
