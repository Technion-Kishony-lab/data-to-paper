import re


def word_count(text: str) -> int:
    """
    Count the number of words in provided test.
    """
    return len(re.findall(r'\w+', text))


def line_count(text: str) -> int:
    """
    Count the number of lines in provided test.
    """
    return len(text.splitlines())


def is_bulleted_list(text: str) -> bool:
    """
    Check if the provided text is a bulleted list, i.e. that there are lines starting with '- ' or '* '.
    """
    return any(line.startswith('- ') or line.startswith('* ') for line in text.splitlines())
