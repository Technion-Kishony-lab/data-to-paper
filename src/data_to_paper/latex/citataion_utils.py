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
