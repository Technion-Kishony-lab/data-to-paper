import re
from typing import Dict, List


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


def remove_tags(text):
    text = re.sub(r'<[^>]+>', '', text)  # Remove HTML tags
    text = re.sub(r'&lt;|&gt;', '', text)  # Remove &lt; and &gt;
    text = re.sub(r'^Abstract', 'Abstract ', text)  # Add space after "Abstract" at the beginning
    text = re.sub(r'^p|/p$', '', text)  # Remove "p" and "/p" at the beginning and end
    return text.strip()  # Remove leading and trailing whitespace
