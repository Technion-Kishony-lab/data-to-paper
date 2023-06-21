import re
from typing import List


def find_citation_ids(latex_string) -> List[str]:
    """
    Find all the citation ids in the latex string.

    For example, if the latex string is
    "one citation \\cite{citation_id1} two citations \\cite{citation_id2, citation_id3}", then the function will return
    ['citation_id1', 'citation_id2', 'citation_id3'].
    """
    pattern = r"\\cite{([^}]+)}"
    matches = re.findall(pattern, latex_string)
    citation_ids = [citation_id.strip() for match in matches for citation_id in match.split(',')]
    return citation_ids


def remove_citations_from_section(section):
    """
    Remove the citations that ChatGPT inserted by mistake.
    """
    section = re.sub(r'\s*\\cite[tp]?(\[.*?])?(\[.*?])?\{[^}]*}(?=\s*\.)?', '', section)
    # also remove \bibliographystyle{} and \bibliography{} commands
    section = re.sub(r'\s*\\bibliographystyle\{.*?\}', '', section)
    section = re.sub(r'\s*\\bibliography\{.*?\}', '', section)
    return section


def get_non_latex_citations(section):
    """
    Get the citations that are not in latex format, i.e., not in the form \cite{citation_id_1, citation_id2}.
    for example find any APA citation in the form (Author, year) or (Author et al., year) or (Author, year, p. 123).
    """
    # find all types of APA citations including without et al. and page number
    pattern = r'\([^\)]*,[^\)]*\)'
    matches = re.findall(pattern, section)
    # check that the matches contains et al. or year
    non_latex_citations = [match.strip() for match in matches if 'et al.' in match or re.search(r'\d{4}', match)]
    return non_latex_citations


def choose_first_citation(sentence_citations):
    """
    Choose the first citation for the sentence, if any.
    """
    chosen_citations_ids = [sentence_citations[0]['bibtex'].split('{')[1].split(',\n')[0]]
    chosen_citations_indices = [0]
    return chosen_citations_ids, chosen_citations_indices


def remove_tags(text):
    text = re.sub(r'<[^>]+>', '', text)  # Remove HTML tags
    text = re.sub(r'&lt;|&gt;', '', text)  # Remove &lt; and &gt;
    text = re.sub(r'^Abstract', 'Abstract ', text)  # Add space after "Abstract" at the beginning
    text = re.sub(r'^p|/p$', '', text)  # Remove "p" and "/p" at the beginning and end
    return text.strip()  # Remove leading and trailing whitespace
