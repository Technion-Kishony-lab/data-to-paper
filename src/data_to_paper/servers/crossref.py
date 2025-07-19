import time
from typing import List, Mapping, Any

import requests
from unidecode import unidecode

from data_to_paper.utils.nice_list import NiceList

from .base_server import ParameterizedQueryServerCaller
from .custom_types import Citation
from .types import ServerErrorException

from data_to_paper.utils.print_to_file import print_and_log_red

CROSSREF_URL = "https://api.crossref.org/works"

HEADERS = {"User-Agent": "data_to_paper (mailto:kishonystud@technion.ac.il)"}

BIBTEX_TEMPLATE = "@{type}{{{id},\n{fields}}}\n"

TYPE_MAPPING = {
    "journal-article": "article",
    "proceedings-article": "inproceedings",
    "book": "book",
    "edited-book": "inbook",
    "book-chapter": "inbook",
}


def get_type_from_crossref(crossref: Mapping[str, Any]) -> str:
    return TYPE_MAPPING.get(crossref["type"], "misc")


PAPER_MAPPING = {
    "authors": "author",
    "title": "title",
    "journal": "journal",
    "year": "year",
    "volume": "volume",
    "issue": "number",
    "pages": "pages",
    "DOI": "doi",
}

BOOK_MAPPING = {
    "authors": "author",
    "editors": "editor",
    "title": "title",
    "publisher": "publisher",
    "year": "year",
    "volume": "volume",
    "issue": "number",
    "pages": "pages",
    "DOI": "doi",
    "ISBN": "isbn",
}


STRS_TO_REMOVE_FROM_BIBTEX_ID = [
    " ",
    "-",
    "_",
    "–",
    "’",
    "'",
    "/",
    " ",
    "(",
    ")",
    "[",
    "]",
    "{",
    "}",
    ":",
    ";",
    ",",
    ".",
    "?",
    "!",
    "“",
    "”",
    '"',
    "–",
]

FORBIDDEN_BIBTEX_IDS = set(
    [
        "None",
        "none",
        "nan",
        "NA",
        "na",
        "N/A",
        "Introduction",
        "introduction",
        "Results",
        "results",
        "Discussion",
        "discussion",
        "Methods",
        "methods",
        "Abstract",
        "abstract",
        "Conclusion",
        "conclusion",
        "Background",
        "background",
        "Acknowledgments",
        "acknowledgments",
        "References",
        "references",
        "Supplementary",
        "supplementary",
        "",
        " ",
    ]
)


class CrossrefCitation(Citation):
    """
    A single crossref citation. This the raw dict after transforming the json response.
    This dict is hashable.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._bibtex_id_override = None  # For handling duplicate IDs

    @property
    def bibtex_type(self) -> str:
        return get_type_from_crossref(self)

    @property
    def bibtex(self) -> str:
        # create a mapping for article and inproceedings
        bibtex_type = get_type_from_crossref(self)
        is_paper = bibtex_type in ["article", "inproceedings"]
        field_mapping = PAPER_MAPPING if is_paper else BOOK_MAPPING

        fields = []
        for key, value in self.items():
            if key in field_mapping:
                if value and key not in ["doi", "isbn"]:
                    # remove special characters of the value
                    if isinstance(value, list):
                        value = [
                            unidecode(v).replace(r" &", r" \&").replace(r"_", r"\_")
                            for v in value
                        ]
                    elif isinstance(value, str):
                        value = (
                            unidecode(value).replace(r" &", r" \&").replace(r"_", r"\_")
                        )
                bibtex_key = field_mapping[key]
                fields.append(f"{bibtex_key} = {{{value}}}")
        return BIBTEX_TEMPLATE.format(
            type=self.bibtex_type, id=self.bibtex_id, fields=",\n".join(fields)
        )

    @property
    def bibtex_id(self) -> str:
        """
        Get the bibtex id for this citation.
        Creates a more descriptive and unique ID to avoid conflicts.
        """
        # Check for override first (used for uniqueness)
        if hasattr(self, "_bibtex_id_override") and self._bibtex_id_override:
            return self._bibtex_id_override

        # Check if we have sufficient metadata for a quality citation
        if not self._has_sufficient_metadata():
            return None  # Signal that this citation should be filtered out

        # Get components with better fallbacks
        first_author = self.get("first_author_family", "")
        if first_author:
            first_author = unidecode(first_author)
            # Clean author name more thoroughly
            first_author = "".join(c for c in first_author if c.isalnum())
            first_author = first_author[:12]  # Limit length
        else:
            first_author = "UnknownAuthor"

        year = str(self.get("year", "")) if self.get("year") else "NoYear"

        # Use multiple meaningful words from title for better uniqueness
        title_words = []
        if self.get("title"):
            # Split title and filter out common words
            common_words = {
                "the",
                "a",
                "an",
                "and",
                "or",
                "but",
                "in",
                "on",
                "at",
                "to",
                "for",
                "of",
                "with",
                "by",
                "is",
                "are",
                "was",
                "were",
                "be",
                "been",
                "being",
            }
            words = self.get("title", "").split()
            meaningful_words = [
                w for w in words if w.lower() not in common_words and len(w) > 2
            ][:3]  # Take up to 3 meaningful words

            if meaningful_words:
                title_words = [unidecode(word) for word in meaningful_words]
                # Clean each word
                title_words = [
                    "".join(c for c in word if c.isalnum()) for word in title_words
                ]
                title_words = [
                    word for word in title_words if len(word) > 1
                ]  # Filter out single letters

        if not title_words:
            title_words = ["NoTitle"]

        # Create more descriptive ID
        title_part = "".join(
            word.capitalize() for word in title_words[:3]
        )  # Use up to 3 words
        bibtex_id = first_author + year + title_part

        # remove special characters from the id
        for char in STRS_TO_REMOVE_FROM_BIBTEX_ID:
            bibtex_id = bibtex_id.replace(char, "")

        # Ensure minimum quality and not forbidden
        if len(bibtex_id) <= 8 or bibtex_id in FORBIDDEN_BIBTEX_IDS:
            # Use DOI-based ID if available (more reliable)
            if self.get("DOI"):
                doi_clean = "".join(c for c in self.get("DOI") if c.isalnum())[-10:]
                bibtex_id = first_author + year + "DOI" + doi_clean
            else:
                # If still not good enough, this citation should be filtered out
                return None

        return bibtex_id

    def _has_sufficient_metadata(self) -> bool:
        """
        Check if this citation has sufficient metadata to be useful.
        """
        # Must have at least title and either author or year
        has_title = bool(self.get("title", "").strip())
        has_author = bool(self.get("first_author_family", "").strip())
        has_year = bool(self.get("year"))

        # Must have title and at least one of author/year
        return has_title and (has_author or has_year)

    @property
    def title(self) -> str:
        """
        Get the title of the citation.
        """
        return self.get("title", "")

    @property
    def abstract(self) -> str:
        """
        Get the abstract of the citation.
        """
        return self.get("abstract", "")

    @property
    def journal(self) -> str:
        """
        Get the journal of the citation.
        """
        return self.get("journal", "")

    @property
    def year(self) -> str:
        """
        Get the year of the citation.
        """
        return self.get("year", "")

    @property
    def influence(self) -> int:
        """
        Get the influence of the citation.
        """
        return self.get("influence", 0)

    @property
    def embedding(self) -> str:
        """
        Get the embedding of the citation.
        """
        return self.get("embedding", None)

    @property
    def tldr(self) -> str:
        """
        TLDR will be the abstract if exists, otherwise the title, otherwise None.
        """
        abstract = self.get("abstract", None)
        if abstract:
            return abstract
        title = self.get("title", None)
        if title:
            return title
        return None


class CrossrefServerCaller(ParameterizedQueryServerCaller):
    """
    Search for citations in Crossref.
    """

    name = "Crossref"
    file_extension = "_crossref.bin"

    @staticmethod
    def crossref_item_to_citation(item: dict) -> dict:
        # create authors as a string in the format
        # "first_name1 last_name1 and first_name2 last_name2 and first_name3 last_name3"
        authors_string = ""
        if item.get("author"):
            for author in item["author"]:
                if author != item["author"][-1]:
                    authors_string += (
                        f"{author.get('given', '')} {author.get('family', '')} and "
                    )
                else:
                    authors_string += (
                        f"{author.get('given', '')} {author.get('family', '')}"
                    )
        first_author = item.get("author", [None])[0]
        first_author_family = first_author.get("family", "") if first_author else ""
        citation = {
            "title": item.get("title", [""])[0],
            "abstract": item.get("abstract", ""),
            "first_author_family": first_author_family,
            "authors": authors_string,
            "journal": item.get("container-title", [None])[0],
            "doi": item.get("DOI", ""),
            "type": item.get("type", ""),
            "year": (
                item["published"]["date-parts"][0][0]
                if "published" in item
                else (
                    item["published-print"]["date-parts"][0][0]
                    if "published-print" in item
                    else ""
                )
            ),
            "publisher": item.get("publisher", ""),
            "volume": item.get("volume", ""),
            "issue": item.get("issue", ""),
            "page": item.get("page", ""),
            "isbn": item.get("ISBN", ""),
        }
        for key, value in citation.items():
            if isinstance(value, str) and "&NA;" in value:
                citation[key] = ""
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
        print_and_log_red(f'QUERYING Crossref FOR: "{query}"', should_log=False)
        for attempt in range(3):
            response = requests.get(CROSSREF_URL, headers=HEADERS, params=params)
            if response.status_code not in (504, 429):
                break
            wait_time = 2**attempt  # Exponential backoff
            print_and_log_red(
                f"ERROR: Server timed out or too many requests. "
                f"We wait for {wait_time} sec and try again.",
                should_log=False,
            )
            time.sleep(wait_time)
        else:
            raise ServerErrorException(
                server=cls.name, response=response
            )  # if we failed all attempts

        if response.status_code != 200:  # 200 is the success code
            raise ServerErrorException(server=cls.name, response=response)

        data = response.json()
        papers = [
            cls.crossref_item_to_citation(item) for item in data["message"]["items"]
        ]

        if len(papers) > 0:  # if there are papers
            papers = [
                paper for paper in papers if CrossrefCitation(paper).bibtex_id != "None"
            ]
            return papers
        else:
            # failing gracefully
            return []

    @staticmethod
    def _post_process_response(
        response: List[dict], args, kwargs
    ) -> List[CrossrefCitation]:
        """
        Post process the response from the server.
        """
        query = args[0] if args else kwargs.get("query", None)
        citations = NiceList(separator="\n", prefix="[\n", suffix="\n]")
        seen_bibtex_ids = set()

        for rank, paper in enumerate(response):
            citation = CrossrefCitation(paper, search_rank=rank, query=query)

            # Check if citation has sufficient metadata
            if citation.bibtex_id is None:
                print_and_log_red(
                    f"Skipping citation with insufficient metadata: {citation.get('title', 'No title')[:50]}"
                )
                continue

            # Ensure uniqueness - if we have a duplicate, modify it
            original_id = citation.bibtex_id
            counter = 1
            while citation.bibtex_id in seen_bibtex_ids:
                citation._bibtex_id_override = (
                    f"{original_id}{chr(65 + counter - 1)}"  # Add A, B, C, etc.
                )
                counter += 1
                if counter > 26:  # Fallback after Z
                    citation._bibtex_id_override = f"{original_id}{counter - 26}"

            seen_bibtex_ids.add(citation.bibtex_id)
            citations.append(citation)

        return citations


CROSSREF_SERVER_CALLER = CrossrefServerCaller()
