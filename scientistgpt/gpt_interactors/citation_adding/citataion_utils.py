import re
from typing import Dict, List

import requests

from .exceptions import ServerErrorCitationException, WrongFormatCitationException, NotInCitationsCitationException


def validate_citation_ids(response, citations_ids):
    """
    Validate that the response is in the correct format and all ids are existing ones.
    """
    if response == '[]':
        return []
    # check that the response has only relevant citations ids
    if not all(citation_id in citations_ids for citation_id in response):
        raise NotInCitationsCitationException(response)
    return response


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

    if item['authors']:
        bibtex_id = item['authors'][0].split(" ")[-1] + (str(item.get("year")) if item.get("year") else "")
        # add also the first word of the title if it exists
        bibtex_id += item['title'].split(" ")[0] if item.get("title") else ""
    else:
        # get the first 3 words of the title if they exist otherwise use the first two, otherwise use the first one
        title_words = item['title'].split(" ")
        if len(title_words) > 3:
            bibtex_id = "".join(title_words[:3])
        elif len(title_words) > 2:
            bibtex_id = "".join(title_words[:2])
        else:
            bibtex_id = title_words[0]
        # add the year if it exists
        bibtex_id += str(item.get("year")) if item.get("year") else ""

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
