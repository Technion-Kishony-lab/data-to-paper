import re
import difflib

import numpy as np


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


def diff_strs(str1: str, str2: str, context: int = 1,
              add_template: str = '\033[91m{}\033[0m ',
              remove_template: str = '\033[92m{}\033[0m ',
              ) -> str:
    """
    Return a string that shows the diff between two strings.
    `context` is the number of words to show before and after a diff.
    `add_template` and `remove_template` are the templates to use for added and removed words.
    """
    d = difflib.Differ()
    diff = list(d.compare(str1.split(), str2.split()))
    is_diff = np.array([word[0] != ' ' for word in diff])

    # to_show is a True/False flag that indicates whether to show the diff or not. it is True if there is a diff, or
    # we are within a distance `context` from a diff.
    to_show = is_diff.copy()
    for i in range(context):
        to_show[1:] |= to_show[:-1]
        to_show[:-1] |= to_show[1:]

    s = ''
    three_dots = False
    for word, show in zip(diff, to_show):
        if show:
            tag, word = word[0], word[2:]
            if tag == ' ':  # no change
                s += word + ' '
            elif tag == '-':  # removed
                s += remove_template.format(word)
            elif tag == '+':  # added
                s += add_template.format(word)
            elif tag == '?':  # ?
                s += f'[{word}] '
            else:
                raise ValueError(f'Unknown tag: {tag}')
            three_dots = False
        else:
            if not three_dots:
                s += ' ... '
                three_dots = True
    return s
