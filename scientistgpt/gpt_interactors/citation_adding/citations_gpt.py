from dataclasses import dataclass
from typing import Dict, List, Optional

import re

from scientistgpt.gpt_interactors.converser_gpt import ConverserGPT
from scientistgpt.utils import dedent_triple_quote_str, extract_text_between_tags
from scientistgpt.user_utils.tag_pairs import DICT_TAG_PAIRS, LIST_TAG_PAIRS

from .exceptions import WrongFormatCitationException, NotInSectionCitationException, NotInCitationsCitationException, \
    ServerErrorCitationException
from .citataion_utils import validate_citation_ids, validate_variable_type, choose_first_citation, crossref_search


@dataclass
class CitationGPT(ConverserGPT):
    """
    Interact with chatgpt to find citations for a specific section in the paper.
    """

    # override the default system prompt:
    system_prompt: str = """
    You are a scientific citation expert. 
    You are given a section of a paper, you should mention what sentences need to be cited.
    You will be provided with list of possible citations, 
    and you should select the most appropriate one for each of the sentences. 
    You will rewrite the sentences with the citations.
    The citations will be inserted to the text using \\cite{}.
    """

    section: str = None
    "The section of the paper to which we are adding citations."

    max_number_of_attempts: int = 4
    max_number_of_api_calls: int = 3

    bibtex_file_path = 'citations.bib'

    sentences_to_queries: Dict[str, str] = None

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
            except NotInSectionCitationException as e:
                feedback_message = \
                    f'You returned sentences that are not in the section: {e.sentences}.'
                continue
            return response_value
        # TODO:  Need to think how we end the conversation on failure
        raise ValueError(f'Could not find sentences after {self.max_number_of_attempts} attempts.')

    def _check_all_sentences_are_in_section(self, sentences_queries):
        """
        Check that all sentences (keys of the dict) are in the section.
        """
        sentences_not_in_section = []
        for sentence in sentences_queries:
            if sentence not in self.section:
                sentences_not_in_section.append(sentence)

        if sentences_not_in_section:
            raise NotInSectionCitationException(sentences=sentences_not_in_section)

    def _find_citations_for_sentences(self) -> Dict[str, List[str]]:
        """
        Find citations for the sentences in sentences_to_queries using their search queries.
        """
        sentences_to_citations = {}
        for sentence_number, (sentence, query) in enumerate(self.sentences_to_queries.items()):
            for number_of_tries in range(self.max_number_of_api_calls):
                try:
                    self.comment(
                        f'Finding citations for sentence {sentence_number + 1}, try number {number_of_tries + 1}.')
                    sentences_to_citations[sentence] = crossref_search(query)
                    break
                except ServerErrorCitationException as e:
                    self.comment(f"CrossRef server error: {e}")
            else:
                self.comment(f"Could not find citations for the sentence:\n{sentence}.")

        return sentences_to_citations

    def _choose_citations_for_sentence(self, sentence, sentence_citations, choose_using_chatgpt=True):
        """
        Choose the most appropriate citations for the sentence, if any.
        """
        chosen_citations_ids = None
        if not choose_using_chatgpt:
            return choose_first_citation(sentence_citations)
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
        for attempt_num in range(self.max_number_of_attempts):
            response = self.conversation_manager.get_and_append_assistant_message()
            try:
                chosen_citations_ids = validate_citation_ids(validate_variable_type(eval(
                    '[' + extract_text_between_tags(response, *LIST_TAG_PAIRS) + ']'), List[str]), citations_ids)
            except SyntaxError:
                self.conversation_manager.append_user_message(dedent_triple_quote_str(
                    """
                    eval(response) mentioned "invalid syntax". 
                    Please try again making sure you return the results with the correct format, i.e., as a list, 
                    like this "["AuthorX2022Title", "AuthorY2009Title"]"
                    """), tag='wrong_format_on_eval')
            except NameError:
                self.conversation_manager.append_user_message(dedent_triple_quote_str(
                    """
                    eval(response) mentioned "name not defined". 
                    Please try again making sure you return the results with the correct format, i.e., as a list, 
                    like this "["AuthorX2022"]"
                    """), tag='wrong_format_on_eval')
            except ValueError:
                self.conversation_manager.append_user_message(dedent_triple_quote_str(
                    """
                    I could not find "{}" and "{}" in your result. 
                    Please try again making sure you return the results with the correct format, i.e., as a list, 
                    like this "["AuthorX2022Title", "AuthorY2009Title"]"
                    """).format(*LIST_TAG_PAIRS),
                                                              tag='wrong_format_no_brackets')
            except WrongFormatCitationException as e:
                self.conversation_manager.append_user_message(dedent_triple_quote_str(
                    """
                    eval(response) got the error {}. 
                    Please try again making sure you return the results with the correct format, i.e., as a list, 
                    like this "["AuthorX2022Title", "AuthorY2009Title"]"
                    """).format(e), tag='wrong_format_wrong_type')
            except NotInCitationsCitationException as e:
                self.conversation_manager.append_user_message(dedent_triple_quote_str(
                    """
                    You returned a citation id that is not in the citations: {}. 
                    Rewrite the answer and make sure to reply with only the citations ids and only ones that exists.
                    """).format(e), tag='not_in_citations_or_wrong_format')
            except Exception as e:
                self.conversation_manager.append_user_message(dedent_triple_quote_str(
                    """
                    Got the error {}. 
                    Please try again making sure you return the results with the correct format, i.e., as a list, 
                    like this "["AuthorX2022Title", "AuthorY2009Title"]"
                    """).format(e), tag='wrong_format')
            else:
                if not chosen_citations_ids:
                    return [], []
                # find the indices of the chosen citations
                chosen_citations_indices = [citations_ids.index(citation_id) for citation_id in chosen_citations_ids]
                # return the chosen citations
                return chosen_citations_ids, chosen_citations_indices
        if chosen_citations_ids is None:
            return choose_first_citation(sentence_citations)

    def _rewrite_sentence_with_citation(self, sentence, citations_titles, citations_ids):
        """
        Rewrite the sentence with the citation.
        """
        self.conversation_manager.append_user_message(
            dedent_triple_quote_str("""
            The sentence you need to rewrite is: "{}".
            As a reminder, the citations papers titles are: "{}".
            The citation ids you should enter in a smart and correct position maintaining good sentence flow are: "{}".
            Please rewrite the sentence with the citations using the citations ids given.
            You should use \\cite{{}}, i.e., keep on correct .tex format to insert the citation, 
            do not reply with any other text beside the rewritten sentence.
            """).format(sentence, citations_titles, citations_ids))
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
        #  TODO: make it sound like a conversartion (give me the sentences you want to cross ref.
        #   I corssref and this is what i got..."
        for sentence, sentence_citations in sentences_to_possible_citations.items()
            chosen_citations_ids, chosen_citations_indices = \
                self._choose_citations_for_sentence(sentence, sentence_citations, choose_using_chatgpt=True)
            # get the chosen citations titles
            chosen_citations_titles = [sentence_citations[index]['title'] for index in chosen_citations_indices]
            if chosen_citations_ids:
                updated_sentence = self._rewrite_sentence_with_citation(sentence, chosen_citations_titles,
                                                                        chosen_citations_ids)
                updated_sentences.append(updated_sentence)
                all_citations_bibtexes.update(
                    [sentence_citations[index]['bibtex'] for index in chosen_citations_indices]
                )
            else:
                updated_sentences.append(sentence)

        # replace the section with the updated sentences
        self.conversation_manager.append_commenter_message(f'Finished rewriting the section with citations, '
                                                           f'replacing the sentences with the rewritten ones.',
                                                           tag='done_rewriting_section')
        updated_section = self.section
        for idx, sentence in enumerate(self.sentences_to_queries):
            updated_section = updated_section.replace(sentence, updated_sentences[idx])

        return updated_section, all_citations_bibtexes
