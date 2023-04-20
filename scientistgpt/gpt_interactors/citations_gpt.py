import os
from dataclasses import dataclass
from typing import Dict, List

import requests
import re

from scientistgpt.gpt_interactors.converser_gpt import ConverserGPT
from scientistgpt.utils import dedent_triple_quote_str
from scientistgpt.user_utils.tag_pairs import TagPairs
from scientistgpt.utils.text_utils import extract_text_between_tags


class WrongFormatError(Exception):
    """
    Error raised when the user did not return the results in the correct format.
    """
    pass


class NotInSectionError(Exception):
    """
    Error raised when the user did not return the results in the correct format.
    """
    pass

class NotInCitations(Exception):
    """
    Error raised when the user did not return the citations that are inside the possible citations.
    """
    pass


def validate_citation_ids(response, citations_ids):
    """
    Validate that the response is in the correct format and all ids are existing ones.
    """
    if response == '[]':
        return []
    # check that the response has only relevant citations ids
    if not all(citation_id in citations_ids for citation_id in response):
        raise NotInCitations(response)
    return response


def find_citations_for_sentences(sentences_queries):
    """
    Find citations for the sentences using the queries.
    """
    sentences_citations = []
    for sentence in sentences_queries:
        sentence_citations = crossref_search(sentences_queries[sentence])
        sentences_citations.append(sentence_citations)
    return sentences_citations


def validate_type_of_response(sentences_queries, format_type):
    """
    Validate that the response is given in the correct format. if not raise WrongFormatError.
    """
    if format_type == Dict[str: str]:
        if not isinstance(sentences_queries, dict) or not all(isinstance(k, str) and isinstance(v, str)
                                                              for k, v in sentences_queries.items()):
            raise WrongFormatError(f'object is not of type: {format_type}')
    elif format_type == List[str]:
        if not isinstance(sentences_queries, list) or not all(isinstance(k, str) for k in sentences_queries):
            raise WrongFormatError(f'object is not of type: {format_type}')
    else:
        return sentences_queries


@dataclass
class CitationGPT(ConverserGPT):
    """
    Interact with chatgpt to find citations for a specific section in the paper.
    """

    # override the default system prompt:
    system_prompt: str = """You are a citation expert. 
                            You are given a section of a paper, you should mention what sentences need to be cited.
                            You will be provided with list of possible citations, and you should select the most 
                            appropriate one for each of the sentences.
                            You will rewrite the sentences with the citations.
                            The citations will be inserted to the text using \\cite{}.
                            """

    section: str = None
    """
    A section to add citations to.
    """

    dict_tag_pairs: TagPairs = TagPairs('{', '}')
    list_tag_pairs: TagPairs = TagPairs('[', ']')

    max_number_of_attempts: int = 3

    bibtex_file_path = 'citations.bib'

    def _remove_citations_in_section(self):
        """
        Remove the citations that were inserted by mistake.
        """
        self.section = re.sub(r'\\cite\{.*?}', '', self.section)

    def _choose_sentences_that_need_citations(self):
        """
        choose sentences that need citations from the section.
        """

        self.conversation_manager.append_user_message(dedent_triple_quote_str("""
        Extract from the given section the sentences that we need to add citations to them. 
        For each of the sentence, create the best query possible for the citation search for this sentence.
        You need to return the list of this sentences and the queries in this format: 
        {
         "This is sentence that need to have reference": "This is the query for this sentence", 
         "This is another important claim": "Some important keywords for this sentence", 
         "This is the another sentence that need to get a source": "This is the best query for this sentence",
         } 
        This just an example, identify as many sentences as you think that need get update with references.
        return only dict of "sentence:query" pairs, without any other text.
        """), tag='select_sentences')

        for attempt_num in range(self.max_number_of_attempts):
            response = self.conversation_manager.get_and_append_assistant_message()
            try:
                # check if the response can be parsed as a list of sentences:
                return self._check_all_sentences_are_in_section(validate_type_of_response(eval(
                    '{' + extract_text_between_tags(response, *self.dict_tag_pairs) + '}'), Dict[str: str]))
            except ValueError:
                self.conversation_manager.append_user_message(
                    f'I could not find "{self.dict_tag_pairs.left_tag}" and "{self.dict_tag_pairs.right_tag}" '
                    f'in your result. \n'
                    f'Please try again making sure you return the results with the correct format, \n'
                    f'like this "{{"sentence 1":"query 1", "sentence 2": "query2"}}"', tag='wrong_format_no_brackets')
            except WrongFormatError as e:
                self.conversation_manager.append_user_message(
                    f'eval(response) got the error {e}. \n'
                    f'Please try again making sure you return the results with the correct format, \n'
                    f'like this "{{"sentence 1":"query 1", "sentence 2": "query2"}}', tag='wrong_format_wrong_type')
            except NotInSectionError as e:
                self.conversation_manager.append_user_message(
                    f'You returned a sentences that are not in the section: {e}. \n'
                    f'Rewrite the answer and make sure to give only sentences that found in the section.',
                    tag='not_in_section')
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
            raise NotInSectionError(f'Sentences: {sentences_not_in_section} are not in the section.')

        return sentences_queries

    def _choose_citations_for_sentence(self, sentence, sentence_citations):
        """
        Choose the most appropriate citations for the sentence, if any.
        """
        citations_ids = [citation['bibtex'].split('{')[1].split('}')[0] for citation in sentence_citations]
        citation_abstracts = [citation['abstract'] for citation in sentence_citations]
        self.conversation_manager.append_user_message(dedent_triple_quote_str("""
        Choose the most appropriate citations for the sentence: 
        
        {}
        
        Choose from the following citations, by reading their abstracts:
        
        {}
        
        Reply in the following format: 
        ['id1', 'id4',...]
        where id1 and id4 are the ids of the citations you choose.
        You can choose one or more, or choose to not add any citations to this sentence by replying with "[]".
        """).format(sentence,
                    '\n'.join(
                        [f"id: '{citation_id}', abstract: '{citation_abstract}'" for citation_id, citation_abstract in
                         zip(citations_ids, citation_abstracts)])
                    ), tag='choose_citations')
        for attempt_num in range(self.max_number_of_attempts):
            response = self.conversation_manager.get_and_append_assistant_message()
            try:
                chosen_citations_ids = validate_citation_ids(validate_type_of_response(eval(
                    '[' + extract_text_between_tags(response, *self.list_tag_pairs) + ']'), List[str]), citations_ids)
            except ValueError:
                self.conversation_manager.append_user_message(
                    f'I could not find "{self.list_tag_pairs.left_tag}" and "{self.list_tag_pairs.right_tag}" '
                    f'in your result. \n'
                    f'Please try again making sure you return the results with the correct format, \n'
                    f'like this "["id3", "id2"]"', tag='wrong_format_no_brackets')
            except WrongFormatError as e:
                self.conversation_manager.append_user_message(
                    f'eval(response) got the error {e}. \n'
                    f'Please try again making sure you return the results with the correct format, \n'
                    f'like this "["id3", "id2"]"', tag='wrong_format_wrong_type')
            except NotInCitations as e:
                self.conversation_manager.append_user_message(
                    f'You returned a citation id that is not in the citations: {e}. \n'
                    f'Rewrite the answer and make sure to reply with only the citations ids and only ones that exists.',
                    tag='not_in_citations_or_wrong_format')

            else:
                if not chosen_citations_ids:
                    return [], []
                # find the indices of the chosen citations
                chosen_citations_indices = [citations_ids.index(citation_id) for citation_id in chosen_citations_ids]
                # return the chosen citations
                return chosen_citations_ids, chosen_citations_indices

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
            You should use \\cite{}, i.e., keep on correct .tex format to insert the citation, 
            do not reply with any other text beside the rewritten sentence.
            """).format(sentence, citations_titles, citations_ids))
        new_sentence = self.conversation_manager.get_and_append_assistant_message()
        return new_sentence

    def _rewrite_section_with_citations_and_return_bibtexes(self):
        """
        Rewrite the section with the citations.
        """
        self._remove_citations_in_section()
        self.initialize_conversation_if_needed()
        self.conversation_manager.append_user_message(dedent_triple_quote_str("""
        This is the section you need to rewrite with citations:
        
        {}
        """).format(self.section), tag='add_section')
        self.conversation_manager.append_surrogate_message('Great, thanks for giving me the section!',
                                                           tag='add_section_surrogate')
        sentences_queries = self._choose_sentences_that_need_citations()
        self.conversation_manager.reset_back_to_tag('add_section_surrogate')
        sentences_possible_citations = find_citations_for_sentences(sentences_queries)
        updated_sentences = []
        all_citations_bibtexes = []
        for sentence, sentence_citations in zip(sentences_queries, sentences_possible_citations):
            chosen_citations_ids, chosen_citations_indices = self._choose_citations_for_sentence(sentence,
                                                                                                 sentence_citations)
            # get the chosen citations titles
            chosen_citations_titles = [sentence_citations[index]['title'] for index in chosen_citations_indices]
            if chosen_citations_ids:
                updated_sentence = self._rewrite_sentence_with_citation(sentence, chosen_citations_titles,
                                                                        chosen_citations_ids)
                updated_sentences.append(updated_sentence)
                all_citations_bibtexes.append([sentence_citations[index]['bibtex'] for index in chosen_citations_indices])
            else:
                updated_sentences.append(sentence)
            self.conversation_manager.reset_back_to_tag('add_section_surrogate')

        # replace the section with the updated sentences
        updated_section = self.section
        for idx, sentence in enumerate(sentences_queries):
            updated_section = updated_section.replace(sentence, updated_sentences[idx])

        return updated_section, all_citations_bibtexes

    def rewrite_section_with_citations(self):
        """
        Rewrite the section with the citations and save all the citations bibtexes to a .bib file.
        """
        updated_section, all_citations_bibtexes = self._rewrite_section_with_citations_and_return_bibtexes()
        self._save_citations_bibtexes_to_file(all_citations_bibtexes)
        return updated_section

    def _save_citations_bibtexes_to_file(self, all_citations_bibtexes):
        """
        Save all the citations bibtexes to a .bib file.
        """
        # create the bibtex file
        bibtex_file = os.path.join(self.bibtex_file_path)
        with open(bibtex_file, 'w') as f:
            for citations_bibtexes in all_citations_bibtexes:
                for bibtex in citations_bibtexes:
                    f.write(bibtex)

def create_bibtex(item):
    bibtex_template = '@{type}{{{id},\n{fields}}}\n'

    type_mapping = {
        'article-journal': 'article',
        'article': 'article',
        'book': 'book',
        'chapter': 'inbook',
        'proceedings-article': 'inproceedings',
        'paper-conference': 'inproceedings',
    }

    field_mapping = {
        'title': 'title',
        'container-title': 'journal' if item['type'] in ['article-journal', 'article'] else 'booktitle',
        'volume': 'volume',
        'issue': 'number',
        'page': 'pages',
        'published-print': 'year',
        'DOI': 'doi',
    }

    bibtex_type = type_mapping.get(item['type'], 'misc')
    bibtex_id = item.get('author', [{}])[0].get('family', item['title'].strip().split()[0]) + item['issued']['date-parts'][0][0]
    fields = [f"author = {{{' and '.join(item['authors'])}}}"]

    for key, value in item.items():
        if key in field_mapping:
            bibtex_key = field_mapping[key]
            fields.append(f"{bibtex_key} = {{{value}}}")

    return bibtex_template.format(type=bibtex_type, id=bibtex_id, fields=',\n'.join(fields))


def remove_tags(text):
    text = re.sub(r'<[^>]+>', '', text)  # Remove HTML tags
    text = re.sub(r'&lt;|&gt;', '', text)  # Remove &lt; and &gt;
    text = re.sub(r'^Abstract', 'Abstract ', text)  # Add space after "Abstract" at the beginning
    text = re.sub(r'^p|/p$', '', text)  # Remove "p" and "/p" at the beginning and end
    return text.strip()  # Remove leading and trailing whitespace


def crossref_search(query, rows=5):
    url = "https://api.crossref.org/works"
    headers = {
        "User-Agent": "ScientistGPT/0.0.1 (mailto:fallpalapp@gmail.com)"
    }
    params = {
        "query": query,
        "rows": rows,
        "sort": "relevance",
        "order": "desc",
        "filter": "has-abstract:true,type:journal-article,type:book,type:posted-content,type:proceedings-article"
    }
    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        raise Exception(f"Request failed with status code {response.status_code}")

    data = response.json()
    items = data['message']['items']
    citations = []

    for item in items:
        item["abstract"] = remove_tags(item.get("abstract"))
        citation = {
            "title": item["title"][0],
            "authors": [f"{author.get('given', '')} {author.get('family', '')}".strip() for author in
                        item.get("author", [])],
            "year": item["published-print"]["date-parts"][0][0] if "published-print" in item else None,
            "journal": item.get("container-title", [None])[0],
            "doi": item["DOI"],
            "abstract": item["abstract"],
            "type": item["type"]
        }
        bibtex_citation = create_bibtex(citation)
        citation["bibtex"] = bibtex_citation
        citations.append(citation)

    return citations
