import requests
from unidecode import unidecode

from scientistgpt.call_servers import ServerCaller

from .exceptions import ServerErrorCitationException

CROSSREF_URL = "https://api.crossref.org/works"

HEADERS = {
    "User-Agent": "ScientistGPT/0.0.1 (mailto:fallpalapp@gmail.com)"
}


def create_bibtex(item):
    bibtex_template = '@{type}{{{id},\n{fields}}}\n'

    type_mapping = {
        'journal-article': 'article',
        'proceedings-article': 'inproceedings',
        'book': 'book',
        'edited-book': 'inbook',
        'book-chapter': 'inbook',
    }

    bibtex_type = type_mapping.get(item['type'], 'misc')

    # create a mapping for article and inproceedings
    if bibtex_type in ['article', 'inproceedings']:
        field_mapping = {
            'authors': 'author',
            'title': 'title',
            'journal': 'journal',
            'year': 'year',
            'volume': 'volume',
            'issue': 'number',
            'pages': 'pages',
            'DOI': 'doi',
        }
    # create a mapping for book and inbook
    else:
        field_mapping = {
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

    fields = []
    for key, value in item.items():
        if value:
            if not key in ['doi', 'isbn']:
                # remove special characters of the value
                if isinstance(value, list):
                    item[key] = [unidecode(v) for v in value]
                elif isinstance(value, str):
                    item[key] = unidecode(value)
        if key in field_mapping:
            bibtex_key = field_mapping[key]
            fields.append(f"{bibtex_key} = {{{value}}}")

    bibtex_id = item['authors'][0].split(" ")[-1] + (str(item.get("year")) if item.get("year") else "")
    bibtex_id += item['title'].split(" ")[0] if item.get("title") else ""

    return bibtex_template.format(type=bibtex_type, id=bibtex_id, fields=',\n'.join(fields))


class CrossrefServerCaller(ServerCaller):
    """
    Search for citations in Crossref.
    """

    file_extension = "_crossref.txt"

    @staticmethod
    def _get_server_response(query, rows=4):
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
        citations = []

        for item in items:
            if item.get("author", None) is None:
                continue
            citation = {
                "title": item["title"][0],
                "authors": [f"{author.get('given', '')} {author.get('family', '')}".strip() for author in
                            item.get("author", [])],
                "journal": item.get("container-title", [None])[0],
                "doi": item["DOI"],
                "type": item["type"],
                "year": item["published"]["date-parts"][0][0] if "published" in item else
                item["published-print"]["date-parts"][0][0] if "published-print" in item else None,
                "publisher": item.get("publisher"),
                "volume": item.get("volume"),
                "issue": item.get("issue"),
                "page": item.get("page"),
                "editors": [f"{editor.get('given', '')} {editor.get('family', '')}".strip() for editor in
                           item.get("editor", [])],
                "isbn": item.get("ISBN")
            }
            bibtex_citation = create_bibtex(citation)
            citation["bibtex"] = bibtex_citation
            citations.append(citation)

        return citations


CROSSREF_SERVER_CALLER = CrossrefServerCaller()
