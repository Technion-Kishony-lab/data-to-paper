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
