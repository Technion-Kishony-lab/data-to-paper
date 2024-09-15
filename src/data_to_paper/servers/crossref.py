from typing import List, Mapping, Any

import requests
from unidecode import unidecode

from .base_server import ParameterizedQueryServerCaller
from .custom_types import Citation
from .types import ServerErrorException

CROSSREF_URL = "https://api.crossref.org/works"

HEADERS = {
    "User-Agent": "data_to_paper (mailto:fallpalapp@gmail.com)"
}

BIBTEX_TEMPLATE = '@{type}{{{id},\n{fields}}}\n'

TYPE_MAPPING = {
    'journal-article': 'article',
    'proceedings-article': 'inproceedings',
    'book': 'book',
    'edited-book': 'inbook',
    'book-chapter': 'inbook',
}


def get_type_from_crossref(crossref: Mapping[str, Any]) -> str:
    return TYPE_MAPPING.get(crossref['type'], 'misc')


PAPER_MAPPING = {
                'authors': 'author',
                'title': 'title',
                'journal': 'journal',
                'year': 'year',
                'volume': 'volume',
                'issue': 'number',
                'pages': 'pages',
                'DOI': 'doi',
            }

BOOK_MAPPING = {
                'authors': 'author',
                'editors': 'editor',
                'title': 'title',
                'publisher': 'publisher',
                'year': 'year',
                'volume': 'volume',
                'issue': 'number',
                'pages': 'pages',
                'DOI': 'doi',
                'ISBN': 'isbn',
            }


STRS_TO_REMOVE_FROM_BIBTEX_ID = ["-", "_", "–", "’", "'", "/", " ", "(", ")", "[", "]", "{", "}", ":", ";",
                                 ",", ".", "?", "!", "“", "”", '"', "–"]


class CrossrefCitation(Citation):
    """
    A single crossref citation. This the raw dict after transforming the json response.
    This dict is hashable.
    """

    @property
    def bibtex_type(self) -> str:
        return get_type_from_crossref(self)

    @property
    def bibtex(self) -> str:
        # create a mapping for article and inproceedings
        bibtex_type = get_type_from_crossref(self)
        is_paper = bibtex_type in ['article', 'inproceedings']
        field_mapping = PAPER_MAPPING if is_paper else BOOK_MAPPING

        fields = []
        for key, value in self.items():
            if key in field_mapping:
                if value and key not in ['doi', 'isbn']:
                    # remove special characters of the value
                    if isinstance(value, list):
                        value = [unidecode(v).replace(r' &', r' \&').replace(r'_', r'\_') for v in value]
                    elif isinstance(value, str):
                        value = unidecode(value).replace(r' &', r' \&').replace(r'_', r'\_')
                bibtex_key = field_mapping[key]
                fields.append(f"{bibtex_key} = {{{value}}}")
        return BIBTEX_TEMPLATE.format(type=self.bibtex_type, id=self.bibtex_id, fields=',\n'.join(fields))

    @property
    def bibtex_id(self) -> str:
        """
        Get the bibtex id for this citation.
        """
        bibtex_id = unidecode(self['first_author_family']) + (str(self.get("year")) if self.get("year") else "")
        bibtex_id += self['title'].split(" ")[0] if self.get("title") else ""

        # remove special characters from the id like -, _, etc.
        for char in STRS_TO_REMOVE_FROM_BIBTEX_ID:
            bibtex_id = bibtex_id.replace(char, "")
        return bibtex_id


class CrossrefServerCaller(ParameterizedQueryServerCaller):
    """
    Search for citations in Crossref.
    """
    name = "Crossref"
    file_extension = "_crossref.bin"

    @staticmethod
    def crossref_item_to_citation(item):
        # create authors as a string in the format
        # "first_name1 last_name1 and first_name2 last_name2 and first_name3 last_name3"
        authors_string = ""
        for author in item["author"]:
            if author != item["author"][-1]:
                authors_string += f"{author.get('given', '')} {author.get('family', '')} and "
            else:
                authors_string += f"{author.get('given', '')} {author.get('family', '')}"

        # if editors are present, add them to the same way as authors
        editor_string = ""
        if item.get("editor", None) is not None:
            for editor in item["editor"]:
                if editor != item["editor"][-1]:
                    editor_string += f"{editor.get('given', '')} {editor.get('family', '')} and "
                else:
                    editor_string += f"{editor.get('given', '')} {editor.get('family', '')}"
        citation = {
            "title": item["title"][0],
            "first_author_family": item["author"][0]["family"].split(" ")[0],
            "authors": authors_string,
            "journal": item.get("container-title", [None])[0],
            "doi": item.get("DOI", ''),
            "type": item.get("type", ''),
            "year": item["published"]["date-parts"][0][0] if "published" in item else
            item["published-print"]["date-parts"][0][0] if "published-print" in item else '',
            "publisher": item.get("publisher", ''),
            "volume": item.get("volume", ''),
            "issue": item.get("issue", ''),
            "page": item.get("page", ''),
            "editors": editor_string if item.get("editor", None) is not None else '',
            "isbn": item.get("ISBN", '')
        }
        for key, value in citation.items():
            if isinstance(value, str) and "&NA;" in value:
                raise ValueError(f"Value {value} for key {key} is not valid")
        return citation

    @classmethod
    def _get_server_response(cls, query, rows=4) -> List[dict]:
        """
        Get the response from the crossref server as a list of CrossrefCitation objects.
        """
        params = {
            "query.bibliographic": query,
            "rows": rows,
            "filter": "type:journal-article,type:proceedings-article,type:book,type:edited-book,type:book-chapter",
            "select": "title,author,container-title,DOI,type,published,published-print,publisher,volume,issue,page,"
                      "editor,ISBN",
        }

        response = requests.get(CROSSREF_URL, headers=HEADERS, params=params)

        if response.status_code != 200:
            raise ServerErrorException(server=cls.name, response=response)

        data = response.json()
        items = data['message']['items']
        citations: List[dict] = []

        for item in items:
            try:
                citation = CrossrefServerCaller.crossref_item_to_citation(item)
            except (KeyError, ValueError):
                continue
            citations.append(citation)

        return citations

    @staticmethod
    def _post_process_response(response: List[dict], args, kwargs) -> List[CrossrefCitation]:
        """
        Post process the response from the server.
        """
        query = args[0] if args else kwargs.get("query", None)
        return [CrossrefCitation(citation, search_rank=rank, query=query) for rank, citation in enumerate(response)]


CROSSREF_SERVER_CALLER = CrossrefServerCaller()
