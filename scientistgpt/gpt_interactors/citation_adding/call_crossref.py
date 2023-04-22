import requests

from scientistgpt.call_servers import ServerCaller

from .exceptions import ServerErrorCitationException

CROSSREF_URL = "https://api.crossref.org/works"

HEADERS = {
    "User-Agent": "ScientistGPT/0.0.1 (mailto:fallpalapp@gmail.com)"
}


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
            "filter": "type:journal-article,type:book,type:posted-content,type:proceedings-article",
            "select": "title,author,container-title,published-print,DOI,type,published",
        }

        response = requests.get(CROSSREF_URL, headers=HEADERS, params=params)

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


CROSSREF_SERVER_CALLER = CrossrefServerCaller()
