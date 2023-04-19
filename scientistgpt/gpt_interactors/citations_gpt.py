from dataclasses import dataclass

import requests
import re

from scientistgpt.gpt_interactors.converser_gpt import ConverserGPT
from scientistgpt.utils import dedent_triple_quote_str


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
                            The citations will be inserted to the text using \cite{}.
                            """

    section: str = None
    """
    A section to add citations to.
    """


    max_number_of_attempts: int = 3


    def _choose_sentences_that_need_citations(self):
        """
        choose sentences that need citations from the section.
        """

        self.initialize_conversation_if_needed()
        self.conversation_manager.append_user_message(dedent_triple_quote_str("""
        Below is a written section, from which you should extract the sentences that need to be cited. 
        You need to return the list of this sentences in this format: 
        { 1:  "This is sentence that need to be cited", 
          2:  "This is another important claim", 
          3:  "This is the last sentence that need to be cited"
        ... } 
        Identify as many sentences as you think that need to be cited.
        
        This is the section:
        
        {self.section}
        """))

        # TODO: continue here
        for attempt_num in range(self.max_number_of_attempts):
            response = self.conversation_manager.get_and_append_assistant_message()
            try:
                return self.extract_triplet_quoted_text(response)
            except ValueError:
                self.conversation_manager.append_user_message(
                    f'You did not extract the {self.description_of_text_to_extract} correctly. \n'
                    f'Please try again making sure the extracted text is flanked by triple quotes, \n'
                    f'like this """extracted text""".', tag='explicit_instruction')
        raise ValueError(f'Could not extract text after {self.max_number_of_attempts} attempts.')

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
    bibtex_id = item.get('DOI', f"{item['title']}_{item.get('published-print', {}).get('date-parts', [['']])[0][0]}")
    bibtex_id = re.sub(r'\W+', '_', bibtex_id)

    fields = []
    fields.append(f"author = {{{' and '.join(item['authors'])}}}")

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
            "authors": [f"{author.get('given', '')} {author.get('family', '')}".strip() for author in item.get("author", [])],
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


query = "word2vec"
citations = crossref_search(query)
for citation in citations:
    print("bibtex:")
    print(citation["bibtex"] + "\n")
    print("abstract:")
    print(citation["abstract"])