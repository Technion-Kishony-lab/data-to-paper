import re
from typing import Dict, List

import requests

from .exceptions import ServerErrorCitationException


def validate_variable_type(sentences_queries, format_type):
    """
    Validate that the response is given in the correct format. if not raise TypeError.
    """
    if format_type == Dict[str, str]:
        if isinstance(sentences_queries, dict) \
                and all(isinstance(k, str) and isinstance(v, str) for k, v in sentences_queries.items()):
            return
    elif format_type == List[str]:
        if isinstance(sentences_queries, list) and all(isinstance(k, str) for k in sentences_queries):
            return
    else:
        raise NotImplementedError(f'format_type: {format_type} is not implemented')
    raise TypeError(f'object is not of type: {format_type}')


def choose_first_citation(sentence_citations):
    """
    Choose the first citation for the sentence, if any.
    """
    chosen_citations_ids = [sentence_citations[0]['bibtex'].split('{')[1].split(',\n')[0]]
    chosen_citations_indices = [0]
    return chosen_citations_ids, chosen_citations_indices


def create_bibtex(item):
    bibtex_template = '@{type}{{{id},\n{fields}}}\n'

    type_mapping = {
        'article-journal': 'article',
        'article': 'article',
        'book': 'book',
        'chapter': 'inbook',
        'proceedings-article': 'inproceedings',
        'paper-conference': 'inproceedings',
        'posted-content': 'online',
    }

    field_mapping = {
        'title': 'title',
        'container-title': 'journal' if item['type'] in ['article-journal', 'article'] else 'booktitle',
        'volume': 'volume',
        'issue': 'number',
        'page': 'pages',
        'year': 'year',
        'DOI': 'doi',
    }

    bibtex_type = type_mapping.get(item['type'], 'misc')

    # Generate a BibTeX ID based on the author's last name and publication year (if available)
    if item['authors']:
        last_name = item['authors'][0].split(" ")[-1]
        year = str(item.get("year")) if item.get("year") else ""
        first_word_of_title = item['title'].split(" ")[0] if item.get("title") else ""
        bibtex_id = f"{last_name}{year}{first_word_of_title}"
    else:
        # If no author is available, use the first few words of the title and the publication year (if available)
        title_words = item['title'].split(" ")
        bibtex_id = "".join(title_words[:min(len(title_words), 3)])
        year = str(item.get("year")) if item.get("year") else ""
        bibtex_id += year

    fields = []
    for key, value in item.items():
        if key in field_mapping:
            bibtex_key = field_mapping[key]
            fields.append(f"{bibtex_key} = {{{value}}}")

    if item['authors']:
        author_list = ' and '.join(item['authors'])
        fields.insert(0, f"author = {{{author_list}}}")

    return bibtex_template.format(type=bibtex_type, id=bibtex_id, fields=',\n'.join(fields))


def remove_tags(text):
    text = re.sub(r'<[^>]+>', '', text)  # Remove HTML tags
    text = re.sub(r'&lt;|&gt;', '', text)  # Remove &lt; and &gt;
    text = re.sub(r'^Abstract', 'Abstract ', text)  # Add space after "Abstract" at the beginning
    text = re.sub(r'^p|/p$', '', text)  # Remove "p" and "/p" at the beginning and end
    return text.strip()  # Remove leading and trailing whitespace


class CallCrossref:
    """
    Search for citations in Crossref.
    Putting the search in a class allows to replace the function with a mock in the tests.
    """
    @staticmethod
    def crossref_search(query, rows=4):
        url = "https://api.crossref.org/works"
        headers = {
            "User-Agent": "ScientistGPT/0.0.1 (mailto:fallpalapp@gmail.com)"
        }
        params = {
            "query.bibliographic": query,
            "rows": rows,
            "filter": "type:journal-article,type:book,type:posted-content,type:proceedings-article",
            "select": "title,author,container-title,published-print,DOI,type,published",
        }
        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            raise ServerErrorCitationException(status_code=response.status_code, text=response.text)

        data = response.json()
        items = data['message']['items']
        citations = []

        for item in items:
            citation = {
                "title": item["title"][0],
                "authors": [f"{author.get('given', '')} {author.get('family', '')}".strip() for author in
                            item.get("author", [])],
                "year": item["published"]["date-parts"][0][0] if "published" in item else
                item["published-print"]["date-parts"][0][0] if "published-print" in item else None,
                "journal": item.get("container-title", [None])[0],
                "doi": item["DOI"],
                "type": item["type"]
            }
            bibtex_citation = create_bibtex(citation)
            citation["bibtex"] = bibtex_citation
            citations.append(citation)

        return citations
