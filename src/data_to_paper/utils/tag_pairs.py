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

    def wrap(self, text: str) -> str:
        """
        Wrap text with the tags.
        """
        return f'{self.left_tag}{text}{self.right_tag}'

    def is_flanking(self) -> bool:
        """
        Check if the tag is flanking.
        """
        return self.right_tag is not None


# String patterns used to wrap text for save and load. Use unique patterns, not likely to occur in conversation.
SAVE_TAGS = TagPairs('START>>>>>\n', '\n<<<<<END\n')
