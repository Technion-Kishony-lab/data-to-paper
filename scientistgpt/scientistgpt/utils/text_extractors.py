FROM_OPEN_BRACKET_TO_CLOSE_BRACKET = {'[': ']', '{': '}', '(': ')'}


def extract_text_between_tags(text: str, left_tag: str, right_tag: str = None, leave_tags: bool = False):
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
            start = text.find(left_tag)
            if start == -1:
                raise ValueError(f'Could not find left tag {left_tag} in text')
            end = text.find(right_tag, start + len(left_tag))
            if end == -1:
                raise ValueError(f'Could not find left tag {right_tag} in text')
            if end - start - len(left_tag) == 0:
                raise ValueError(f'Could not find left tag {left_tag} in text')
            if leave_tags:
                return text[start:end + len(right_tag)]
            return text[start + len(left_tag):end]
        else:
            # use extract_text_between_brackets to extract the text between the brackets
            if leave_tags:
                return left_tag + extract_text_between_brackets(text, left_bracket) + right_tag
            return extract_text_between_brackets(text, left_bracket)
    else:
        # right tag is None, so we return the text from the left tag to the end of the text
        start = text.find(left_tag)
        if start == -1:
            raise ValueError(f'Could not find left tag {left_tag} in text')
        if leave_tags:
            return left_tag + text[start + len(left_tag):]
        return text[start + len(left_tag):]


def extract_text_between_brackets(text: str, open_bracket: str, leave_brackets: bool = False):
    """
    use stack to find matching closing bracket for the first open bracket, use stack to find matching closing bracket.
    return the text between the first open bracket and the matching closing bracket without the brackets.
    """
    start = text.find(open_bracket)
    if start == -1:
        raise ValueError(f'Could not find open bracket {open_bracket} in text')
    end = start + 1
    stack = [open_bracket]
    while len(stack) > 0:
        if text[end] == open_bracket:
            stack.append(open_bracket)
        elif text[end] == FROM_OPEN_BRACKET_TO_CLOSE_BRACKET[open_bracket]:
            stack.pop()
        end += 1
    if leave_brackets:
        return text[start:end]
    return text[start + 1:end - 1]


def extract_first_lines(text: str, num_lines: int = 1):
    """
    Extract the first num_lines lines from the text.
    """
    return '\n'.join(text.splitlines()[:num_lines])


def extract_to_nearest_newline(text: str, end: int):
    """
    Extract the text from the beginning of the text to the nearest newline before end.
    If no newline is found, extract the text from the beginning of the text to end.
    """
    newline_before_end = text.rfind('\n', 0, end)
    if newline_before_end == -1:
        return text[:end]
    return text[:newline_before_end]
