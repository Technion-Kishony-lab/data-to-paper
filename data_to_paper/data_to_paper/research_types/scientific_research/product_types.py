from dataclasses import dataclass
from typing import List, Dict, Any

from data_to_paper.base_products.product import Product, SingleValueProduct
from data_to_paper.servers.custom_types import Citation


@dataclass
class GoalAndHypothesisProduct(SingleValueProduct):
    name: str = "Goal and Hypothesis"

    def _get_content_as_text(self, level):
        return self.value.replace('###', '#' * level)

    def to_extracted_test(self):
        return self.value

    @classmethod
    def from_extracted_test(cls, text):
        return cls(text)


@dataclass
class MostSimilarPapersProduct(SingleValueProduct):
    name: str = "Most Similar Papers"
    value: List[Citation] = None

    def _get_citations(self, is_html=False):
        return '\n'.join(citation.pretty_repr(
            fields=('bibtex_id', 'title', 'journal_and_year', 'tldr'),
            is_html=is_html,
        ) for citation in self.value)

    def _get_content_as_text(self, level: int, **kwargs):
        return self._get_citations(is_html=False)

    def _get_content_as_html(self, level: int, **kwargs):
        return self._get_citations(is_html=True)


@dataclass
class NoveltyAssessmentProduct(SingleValueProduct):
    name: str = "Novelty Assessment"
    value: Dict[str, Any] = None

    def _get_content_as_markdown(self, level: int, **kwargs):
        results = self.value
        level_str = '#' * (level + 1)
        s = ''
        s += f'{level_str} Similarities:\n'
        for similarity in results["similarities"]:
            s += f'- {similarity}\n'
        s += f'{level_str} Differences:\n'
        for difference in results["differences"]:
            s += f'- {difference}\n'
        s += f'{level_str} Choice:\n- {results["choice"]}\n'
        s += f'{level_str} Explanation:\n- {results["explanation"]}\n'
        return s


@dataclass
class HypothesisTestingPlanProduct(SingleValueProduct):
    name: str = 'Hypothesis Testing Plan'

    def _get_content_as_markdown(self, level: int, **kwargs):
        s = ''
        for hypothesis, test in self.value.items():
            s += f'{"#" * (level + 1)} Hypothesis:\n{hypothesis}\n'
            s += f'{"#" * (level + 1)} Test:\n{test}\n\n'
        return s
