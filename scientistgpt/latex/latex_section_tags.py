from typing import List, Dict

from scientistgpt.user_utils.tag_pairs import TagPairs

SECTIONS_TO_TAG_PAIR_OPTIONS: Dict[str, List[TagPairs]] = {
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
