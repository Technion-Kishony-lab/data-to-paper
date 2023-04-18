from typing import Optional, List, Dict, NamedTuple


class TagPairs(NamedTuple):
    left_tag: str
    right_tag: Optional[str]

    def __str__(self):
        if self.right_tag is None:
            return f'`{self.left_tag}`'
        else:
            return f'`{self.left_tag}` and `{self.right_tag}`'


SECTIONS_TO_TAG_PAIR_OPTIONS: Dict[str: List[TagPairs]] = {
    'title': [TagPairs('\\title{', '}')],
    'abstract': [TagPairs('\\begin{abstract}', '\\end{abstract}')]
}


def get_list_of_tag_pairs_for_section(section: str) -> List[TagPairs]:
    """
    Get a list with different options for tag pairs enclosing the specified section.
    """
    if section in SECTIONS_TO_TAG_PAIR_OPTIONS:
        return SECTIONS_TO_TAG_PAIR_OPTIONS[section]
    else:
        return [TagPairs(f'\\section{{{section.capitalize()}}}', None),
                TagPairs(f'\\section*{{{section.capitalize()}}}', None)]
