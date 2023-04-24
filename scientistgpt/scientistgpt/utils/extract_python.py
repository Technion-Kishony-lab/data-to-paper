from typing import Optional, Any, Dict, List

from scientistgpt.utils import extract_text_between_tags
from scientistgpt.utils.tag_pairs import TagPairs


TYPES_TO_TAG_PAIRS: Dict[type, TagPairs] = {
    dict: TagPairs('{', '}'),
    list: TagPairs('[', ']'),
    tuple: TagPairs('(', ')'),
    set: TagPairs('{', '}'),
}


def get_origin(t: type) -> type:
    """
    Get the origin of a type.

    For example, get_origin(List[str]) is list.
    """
    if hasattr(t, '__origin__'):
        return t.__origin__
    return t


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


def extract_python_value_from_response(response: str, value_type: type) -> (Optional[str], Any):
    """
    Extracts a python value from a response string.

    Returns a tuple of (feedback_message, value). If feedback_message is None, then the value was
    successfully extracted. Otherwise, the value is None and feedback_message is a string explaining
    why the value could not be extracted.
    """

    parent_type = get_origin(value_type)
    tags = TYPES_TO_TAG_PAIRS.get(parent_type)
    try:
        response = extract_text_between_tags(response, *tags, leave_tags=True)
    except ValueError:
        feedback_message = \
            f'Your response should be formatted as a {parent_type}, flanked by "{tags[0]}" and "{tags[1]}".'
        return feedback_message, None
    try:
        response_value = eval(response)
    except Exception as e:
        feedback_message = \
            f'I tried to eval your response, `eval(response)`, but got:\n{e}'
        return feedback_message, None
    if not isinstance(response_value, parent_type):
        feedback_message = \
            f'Your response should be formatted as a {parent_type}, but I got a {type(response_value)}.'
        return feedback_message, None
    try:
        validate_variable_type(response_value, value_type)
    except TypeError:
        feedback_message = \
            f'Your response should be formatted as {value_type}.'
        return feedback_message, None

    return None, response_value
