from typing import NamedTuple, Optional


class TagPairs(NamedTuple):
    """
    end strings to extract from text.
    if right_tag=None - extract to the end.
    """
    left_tag: str
    right_tag: Optional[str]

    def __str__(self):
        if self.right_tag is None:
            return f'`{self.left_tag}`'
        else:
            return f'`{self.left_tag}` and `{self.right_tag}`'


DICT_TAG_PAIRS = TagPairs('{', '}')
LIST_TAG_PAIRS = TagPairs('[', ']')
