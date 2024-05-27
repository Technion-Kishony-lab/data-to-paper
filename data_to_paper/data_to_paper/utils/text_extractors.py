import re

FROM_OPEN_BRACKET_TO_CLOSE_BRACKET = {'[': ']', '{': '}', '(': ')'}


def find_str(text: str, query: str, start: int = 0, end: int = None, case_sensitive: bool = True) -> int:
    if not case_sensitive:
        text = text.lower()
        query = query.lower()
    if end is None:
        end = len(text)
    return text.find(query, start, end)


def extract_text_between_most_flanking_tags(text: str, left_tag: str, right_tag: str = None, keep_tags: bool = False,
                                            case_sensitive: bool = True) -> str:
    """
    Extract text between the first left tag and the last right tag.
    """
    start = find_str(text, left_tag, case_sensitive=case_sensitive)
    if start == -1:
        raise ValueError(f'Could not find left tag {left_tag} in text')
    end = text.rfind(right_tag)
    if end == -1:
        raise ValueError(f'Could not find right tag {right_tag} in text')
    if keep_tags:
        return text[start:end + len(right_tag)]
    return text[start + len(left_tag):end]


def extract_text_between_tags(text: str, left_tag: str, right_tag: str = None, keep_tags: bool = False,
                              case_sensitive: bool = True) -> str:
    """
    Extract text between two tags.
    If the right tag is None, then extract text from the left tag to the end of the text
    We also take in account nested brackets.
    """
    optional_brackets = {'[': ']', '{': '}', '(': ')'}
    left_bracket = left_tag[-1]
    if right_tag is not None:
        right_bracket = right_tag[-1]
        if left_bracket not in optional_brackets.keys() or right_bracket != optional_brackets[left_bracket]:
            # just find the first instance of the right tag and return the text between the left tag and the right tag
            start = find_str(text, left_tag, case_sensitive=case_sensitive)
            if start == -1:
                raise ValueError(f'Could not find left tag {left_tag} in text')
            end = find_str(text, right_tag, start + len(left_tag), case_sensitive=case_sensitive)
            if end == -1:
                raise ValueError(f'Could not find left tag {right_tag} in text')
            if end - start - len(left_tag) == 0:
                raise ValueError(f'Could not find left tag {left_tag} in text')
            if keep_tags:
                return text[start:end + len(right_tag)]
            return text[start + len(left_tag):end]
        else:
            return extract_text_between_brackets(text, left_tag, keep_tags=keep_tags)
    else:
        # right tag is None, so we return the text from the left tag to the end of the text
        start = find_str(text, left_tag, case_sensitive=case_sensitive)
        if start == -1:
            raise ValueError(f'Could not find left tag {left_tag} in text')
        if keep_tags:
            return left_tag + text[start + len(left_tag):]
        return text[start + len(left_tag):]


def extract_text_between_brackets(text: str, open_tag: str, keep_tags: bool = False):
    """
    use stack to find matching closing bracket for the first open bracket, use stack to find matching closing bracket.
    return the text between the first open bracket and the matching closing bracket without the brackets.
    """
    start = text.find(open_tag)
    if start == -1:
        raise ValueError(f'Could not find open bracket {open_tag} in text')
    end = start + len(open_tag)
    open_bracket = open_tag[-1]
    close_bracket = FROM_OPEN_BRACKET_TO_CLOSE_BRACKET[open_bracket]
    stack = [open_bracket]
    while len(stack) > 0:
        if end == len(text):
            raise ValueError(f'Could not find matching closing bracket for open bracket {open_bracket} in text')
        if text[end] == open_bracket:
            stack.append(open_bracket)
        elif text[end] == close_bracket:
            stack.pop()
        end += 1
    if keep_tags:
        return text[start:end]
    return text[start + len(open_tag):end - 1]


def extract_all_external_brackets(text: str, open_bracket: str, close_bracket: str = None, open_phrase: str = None):
    """
    Extract all text between the open bracket and the matching closing bracket.
    For example, if open_bracket is '[', and text is 'hello [world [inner]], what is your [name]', then return
    ['[world [inner]]', '[name]'].
    if there are no open brackets, return an empty list.
    """
    if close_bracket is None:
        close_bracket = FROM_OPEN_BRACKET_TO_CLOSE_BRACKET[open_bracket]
    if open_phrase is None:
        open_phrase = open_bracket
    start = text.find(open_phrase)
    if start == -1:
        return []
    end = start + len(open_phrase)
    stack = [open_bracket]
    while len(stack) > 0:
        if end == len(text):
            return []
        if text[end] == open_bracket:
            stack.append(open_bracket)
        elif text[end] == close_bracket:
            stack.pop()
        end += 1
    return [text[start:end]] + extract_all_external_brackets(text[end:], open_bracket, close_bracket, open_phrase)


def _extract_to_nearest(text: str, max_length: int, char: str = '\n'):
    """
    Extract the text from the beginning of the text to the nearest char before end.
    If no char is found, extract the text from the beginning of the text to end.
    if max_length is negative, extract the text from the end of the text to the nearest char before end.
    """
    if abs(max_length) > len(text):
        return text
    if max_length >= 0:
        text = text[:max_length]
        end = text.rfind(char) if char in text else max_length
        return text[:end]
    else:
        text = text[max_length:]
        end = text.find(char) + 1 if char in text else max_length
        return text[end:]


def extract_to_nearest_newline(text: str, end: int):
    """
    Extract the text from the beginning of the text to the nearest newline before end.
    If no newline is found, extract the text from the beginning of the text to end.
    """
    return _extract_to_nearest(text, end, '\n')


def extract_to_nearest_space(text: str, end: int):
    """
    Extract the text from the beginning of the text to the nearest space before end.
    If no space is found, extract the text from the beginning of the text to end.
    """
    return _extract_to_nearest(text, end, ' ')


def get_dot_dot_dot_text(text: str, start: int, end: int):
    """
    Get the text from the beginning of the text to the nearest space before start and from the nearest space after end
    to the end of the text.
    """
    fill = ' [...] '
    start -= len(fill)
    text = re.sub(' +', ' ', text)
    text = text.replace('\n', ' ').replace('```', '').strip()
    if start - end + len(fill) > len(text):
        return text
    return extract_to_nearest_space(text, start) + fill + extract_to_nearest_space(text, end)
