from dataclasses import dataclass
from typing import List, Mapping, Any

import requests
from unidecode import unidecode

from g3pt.exceptions import ScientistGPTException

from .base_server import ServerCaller


CROSSREF_URL = "https://api.crossref.org/works"

HEADERS = {
    "User-Agent": "ScientistGPT/0.0.1 (mailto:fallpalapp@gmail.com)"
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


@dataclass
class ServerErrorCitationException(ScientistGPTException):
    """
    Error raised server wasn't able to respond.
    """
    status_code: int
    text: str

    def __str__(self):
        return f"Request failed with status code {self.status_code}, error: {self.text}"


class CrossrefCitation(dict):
    """
    A single crossref citation. This the raw dict after transforming the json response.
    This dict is hashable.
    """

    def __key(self):
        # TODO: create a tuple of the items, make sure there are no lists within the tuple, otherwise it won't be
        #  hashable the way to deal with that is converting everything inside the list to tuples
        return tuple((k, tuple(v) if isinstance(v, list) else v) for k, v in self.items())

    def __hash__(self):
        return hash(self.__key())

    @property
    def bibtex_type(self):
        return get_type_from_crossref(self)

    def create_bibtex(self):
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
        return BIBTEX_TEMPLATE.format(type=self.bibtex_type, id=self.get_bibtex_id(), fields=',\n'.join(fields))

    def get_bibtex_id(self) -> str:
        """
        Get the bibtex id for this citation.
        """
        bibtex_id = unidecode(self['first_author_family']) + (str(self.get("year")) if self.get("year") else "")
        bibtex_id += self['title'].split(" ")[0] if self.get("title") else ""
        return bibtex_id

    def __str__(self):
        return f'id: "{self.get_bibtex_id()}", title: "{self["title"]}"'

    def __repr__(self):
        return self.__str__()


class CrossrefServerCaller(ServerCaller):
    """
    Search for citations in Crossref.
    """

    file_extension = "_crossref.txt"

    @staticmethod
    def _get_server_response(query, rows=4) -> List[dict]:
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
            raise ServerErrorCitationException(status_code=response.status_code, text=response.text)

        data = response.json()
        items = data['message']['items']
        citations: List[dict] = []

        for item in items:
            if item.get("author", None) is None:
                continue
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
            citations.append(citation)

        return citations

    @staticmethod
    def _post_process_response(response: List[dict]) -> List[CrossrefCitation]:
        """
        Post process the response from the server. This is used to remove duplicates.
        """
        return [CrossrefCitation(citation) for citation in response]


CROSSREF_SERVER_CALLER = CrossrefServerCaller()
