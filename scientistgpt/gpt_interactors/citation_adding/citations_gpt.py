from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

import re

from scientistgpt.gpt_interactors.converser_gpt import ConverserGPT
from scientistgpt.utils import dedent_triple_quote_str, extract_text_between_tags
from scientistgpt.user_utils.tag_pairs import DICT_TAG_PAIRS, LIST_TAG_PAIRS

from .exceptions import NotInOptionsException, ServerErrorCitationException
from .citataion_utils import validate_variable_type, choose_first_citation, crossref_search
from scientistgpt.env import CHOOSE_CITATIONS_USING_CHATGPT, USE_CHATGPT_FOR_CITATION_REWRITING
from .exceptions import WrongFormatCitationException, NotInSectionException, NotInCitationsCitationException, \
    ServerErrorCitationException
from .citataion_utils import validate_citation_ids, validate_variable_type, choose_first_citation, CallCrossref


@dataclass
class CitationGPT(ConverserGPT):
    """
    Interact with chatgpt to find citations for a specific section in the paper.
    """
    agent = 'citation_adding'

    # override the default system prompt:
    system_prompt: str = dedent_triple_quote_str("""
    You are a scientific citation expert. 
    You are given a section of a paper, you should mention what sentences need to be cited.
    You will be provided with list of possible citations, 
    and you should select the most appropriate one for each of the sentences. 
    You will rewrite the sentences with the citations.
    The citations will be inserted to the text using \\cite{}.
    """)

    section: str = None
    "The section of the paper to which we are adding citations."

    max_number_of_attempts: int = 4
    max_number_of_api_calls: int = 3

    bibtex_file_path = 'citations.bib'

    sentences_to_queries: Dict[str, str] = None

    current_sentence_citations_ids: Set[str] = field(default_factory=set)
    sentences_to_add_citations_to: Set[Tuple[str, str]] = field(default_factory=set)

    def _remove_citations_from_section(self):
        """
        Remove the citations that ChatGPT inserted by mistake.
        """
        self.section = re.sub(r'\s*\\cite[tp]?(\[.*?])?(\[.*?])?\{[^}]*}(?=\s*\.)?', '', self.section)

    def _choose_sentences_that_need_citations(self):
        """
        Choose sentences that need citations from the section.
        """
        self.conversation_manager.append_user_message(dedent_triple_quote_str("""
            Extract from the given section the factual sentences to which we need to add citations. 
            For each of the chosen sentence, create the best query possible for the citation search for this sentence.
            You need to return a dict of these sentences mapped to their respective queries.
            Your response should be in the following format: 
            {
             "This is a sentence that needs to have references": "Query for searching citations for this sentence", 
             "This is another important claim": "Some important keywords for this sentence", 
             "This is the another factual sentence that needs a source": "This is the best query for this sentence",
             } 
            This is of course just an example. 
            Identify all the sentences that you think we need to add citations to.
            Remember, you are the author of this paper, you can't cite previous papers of yours, 
            so "We \\cite{}, showed..." is not a valid citation to add.

            Return only a dict of "sentence: query" pairs, without any other text.
            """), tag='select_sentences')

        feedback_message: Optional[str] = None
        for attempt_num in range(self.max_number_of_attempts):
            if feedback_message is not None:
                self.conversation_manager.append_user_message(feedback_message + dedent_triple_quote_str("""
                    Please try again making sure you return the results with the correct format, 
                    like this:
                    ``` 
                    {"sentence extracted from the section": "query of the key sentence", 
                    "another sentence extracted from the section": "the query of this sentence"}
                    ```
                    """), tag='wrong_format')
            response = self.conversation_manager.get_and_append_assistant_message()
            try:
                response = extract_text_between_tags(response, *DICT_TAG_PAIRS, leave_tags=True)
            except ValueError:
                feedback_message = \
                    'Your response should be formatted as a dict, flanked by "{" and "}".'
                continue
            try:
                response_value = eval(response)
            except Exception as e:
                feedback_message = \
                    f'I tried to eval your response, `eval(response)`, but got:\n{e}'
                continue
            try:
                validate_variable_type(response_value, Dict[str, str])
            except TypeError:
                feedback_message = \
                    'Your response should be formatted as a dict containing only strings, as both keys and values.'
                continue
            try:
                self._check_all_sentences_are_in_section(response_value)
            except NotInOptionsException as e:
                feedback_message = \
                    f'You also returned sentences that are not in the section: {e.not_in_options}.' \
                    f'In your following answer return only these sentences fixed.'
                continue
            return response_value
        if not self.sentences_to_add_citations_to:
            # TODO: decide what to do if we didn't find any sentences
            raise ValueError(f'Could not find any sentences after {self.max_number_of_attempts} attempts.')
        return dict(self.sentences_to_add_citations_to)

    def _check_all_sentences_are_in_section(self, sentences_queries):
        """
        Check that all sentences (keys of the dict) are in the section.
        """
        sentences_in_section = []
        sentences_not_in_section = []
        for sentence in sentences_queries:
            if sentence not in self.section:
                sentences_not_in_section.append(sentence)
            else:
                sentences_in_section.append(sentence)
        self.sentences_to_add_citations_to |= \
            set((sentence_in_section, sentences_queries[sentence_in_section])
                for sentence_in_section in sentences_in_section)
        if sentences_not_in_section:
            raise NotInOptionsException(not_in_options=sentences_not_in_section)

    def _find_citations_for_sentences(self) -> Dict[str, List[str]]:
        """
        Find citations for the sentences in sentences_to_queries using their search queries.
        """
        possible_citations = {}
        for sentence_number, (sentence, query) in enumerate(self.sentences_to_queries.items()):
            for number_of_tries in range(self.max_number_of_api_calls):
                try:
                    self.comment(
                        f'Finding citations for sentence {sentence_number + 1}, try number {number_of_tries + 1}.')
                    sentences_to_citations[sentence] = CallCrossref.crossref_search(query)
                    break
                except ServerErrorCitationException as e:
                    self.comment(f"CrossRef server error: {e}")
            else:
                self.comment(f"Could not find citations for the sentence:\n{sentence}.")

        return possible_citations

    def _choose_citations_for_sentence(self, sentence, sentence_citations):
        """
        Choose the most appropriate citations for the sentence, if any.
        """
        self.current_sentence_citations_ids = set()
        if not CHOOSE_CITATIONS_USING_CHATGPT:
            return choose_first_citation(sentence_citations)
        provided_choice = False
        citations_ids = [citation['bibtex'].split('{')[1].split(',\n')[0] for citation in sentence_citations]
        citations_titles = [citation['title'] for citation in sentence_citations]
        self.conversation_manager.append_user_message(dedent_triple_quote_str("""
        Choose the most appropriate citations to add for the sentence: 

        {}

        Choose from the following citations, by reading their titles:

        {}

        Reply in the following format: 
        "["AuthorX2022", "AuthorY2009"]"
        where AuthorX2022 and AuthorY2009 are the ids of the citations you choose.
        You can choose one or more, or choose to not add any citations to this sentence by replying with "[]".
        Choose only citations that are highly relevant to the sentence.
        """).format(sentence,
                    '\n'.join(
                        [f"id: '{citation_id}', title: '{citation_title}'" for citation_id, citation_title in
                         zip(citations_ids, citations_titles)])
                    ), tag='choose_citations')
        feedback_message: Optional[str] = None
        for attempt_num in range(self.max_number_of_attempts):
            if feedback_message is not None:
                self.conversation_manager.append_user_message(feedback_message + dedent_triple_quote_str("""
                    Please try again making sure you return the results with the correct format, 
                    like this:
                    ``` 
                    ["AuthorX2022Title", "AuthorY2009Title"]
                    ```
                    """), tag='wrong_format')
            response = self.conversation_manager.get_and_append_assistant_message()
            try:
                response = extract_text_between_tags(response, *LIST_TAG_PAIRS, leave_tags=True)
            except ValueError:
                feedback_message = \
                    'Your response should be formatted as a list, flanked by "[" and "]".'
                continue
            try:
                response_value = eval(response)
            except Exception as e:
                feedback_message = \
                    f'I tried to eval your response, `eval(response)`, but got:\n{e}'
                continue
            try:
                validate_variable_type(response_value, List[str])
            except TypeError:
                feedback_message = \
                    'Your response should be formatted as a list containing only strings.'
                continue
            try:
                self._validate_citation_ids(response_value, citations_ids)
            except NotInOptionsException as e:
                feedback_message = \
                    f'You returned these citations that are not in the given options: {e.not_in_options}. ' \
                    f'The options are: {citations_ids}.'
                continue
            self.current_sentence_citations_ids |= set(response_value)
            provided_choice = True
            break
        if not provided_choice:
            return choose_first_citation(sentence_citations)
        if not self.current_sentence_citations_ids:
            return [], []
        # find the indices of the chosen citations
        chosen_citations_indices = \
            [citations_ids.index(citation_id) for citation_id in self.current_sentence_citations_ids]
        # return the chosen citations
        return self.current_sentence_citations_ids, chosen_citations_indices

    def _rewrite_sentence_with_citation(self, sentence, citations_ids):
        """
        Rewrite the sentence with the citation.
        """
        if not USE_CHATGPT_FOR_CITATION_REWRITING:
            # add the citations to the end of the sentence as is.
            return sentence.rstrip('.') + ' ' + '\\cite{' + ', '.join(citations_ids) + '.' + '}'

        self.conversation_manager.append_user_message(
            dedent_triple_quote_str("""
            The sentence you need to rewrite is: "{}".
            The citation ids you should enter in a smart and correct position maintaining good sentence flow are: "{}".
            Please rewrite the sentence with the citations using the citations ids given.
            You should use \\cite{{}}, i.e., keep on correct .tex format to insert the citation. 
            Return only the rewritten sentence, do not return the whole section.
            """).format(sentence, citations_ids))
        new_sentence = self.conversation_manager.get_and_append_assistant_message()
        if len(new_sentence) >= len(self.section):
            self.conversation_manager.append_user_message(
                dedent_triple_quote_str("""
                You returned the whole section rewritten, Please return only the rewritten sentence.
                """))
            new_sentence = self.conversation_manager.get_and_append_assistant_message()
        return new_sentence

    def rewrite_section_with_citations(self):
        """
        Rewrite the section with the citations.
        """
        self._remove_citations_from_section()
        self.initialize_conversation_if_needed()
        self.conversation_manager.append_user_message(
            dedent_triple_quote_str("""
                This is the section you need to reformat with citations:

                {}
                """).format(self.section),
            tag='add_section')
        self.conversation_manager.append_surrogate_message(
            'Great, thanks for providing me with the section!', tag='add_section_surrogate')
        self.sentences_to_queries = self._choose_sentences_that_need_citations()
        self.conversation_manager.reset_back_to_tag('add_section_surrogate')
        sentences_to_possible_citations = self._find_citations_for_sentences()
        updated_sentences = []
        all_citations_bibtexes = set()
        #  TODO: make it sound like a conversation (give me the sentences you want to cross ref.
        #   I corssref and this is what i got..."
        for sentence, sentence_citations in sentences_to_possible_citations.items():
            chosen_citations_ids, chosen_citations_indices = \
                self._choose_citations_for_sentence(sentence, sentence_citations)
            if chosen_citations_ids:
                updated_sentence = self._rewrite_sentence_with_citation(sentence, chosen_citations_ids)
                updated_sentences.append(updated_sentence)
                all_citations_bibtexes.update(
                    [sentence_citations[index]['bibtex'] for index in chosen_citations_indices]
                )
            else:
                updated_sentences.append(sentence)
            self.conversation_manager.reset_back_to_tag('add_section_surrogate')

        # replace the section with the updated sentences
        self.conversation_manager.append_commenter_message(
            'Finished rewriting the sentences with citations, replacing the sentences with the rewritten ones.',
            tag='done_rewriting_section')
        updated_section = self.section
        for idx, sentence in enumerate(self.sentences_to_queries):
            updated_section = updated_section.replace(sentence, updated_sentences[idx])

        return updated_section, all_citations_bibtexes

    def _validate_citation_ids(self, response, citations_ids):
        """
        Validate that the response is in the correct format and all ids are existing ones.
        """
        if response == '[]':
            return []
        # check that the response has only relevant citations ids
        in_citations = [citation_id for citation_id in response if citation_id in citations_ids]
        self.current_sentence_citations_ids |= set(in_citations)
        not_in_citations = [citation_id for citation_id in response if citation_id not in citations_ids]
        if not_in_citations:
            raise NotInOptionsException(not_in_options=not_in_citations)
        return response
