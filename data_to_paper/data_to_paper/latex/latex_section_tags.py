from typing import List, Dict

from data_to_paper.utils.tag_pairs import TagPairs

SECTIONS_OR_FRAGMENTS_TO_TAG_PAIR_OPTIONS: Dict[str, List[TagPairs]] = {
    'title': [TagPairs('\\title{', '}')],
    'abstract': [TagPairs('\\begin{abstract}', '\\end{abstract}')],
    'table': [TagPairs('\\begin{table}', '\\end{table}')]
}


def get_list_of_tag_pairs_for_section_or_fragment(section_or_fragment: str) -> List[TagPairs]:
    """
    Get a list with different options for tag pairs enclosing the specified section.
    """
    if section_or_fragment in SECTIONS_OR_FRAGMENTS_TO_TAG_PAIR_OPTIONS:
        return SECTIONS_OR_FRAGMENTS_TO_TAG_PAIR_OPTIONS[section_or_fragment]
    else:
        return [TagPairs(f'\\section{{{section_or_fragment.capitalize()}}}', None),
                TagPairs(f'\\section*{{{section_or_fragment.capitalize()}}}', None)]
