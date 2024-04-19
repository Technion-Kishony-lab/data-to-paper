from dataclasses import dataclass
from typing import List, Dict, Any

from data_to_paper.base_products.product import ValueProduct, Product
from data_to_paper.conversation.stage import Stage
from data_to_paper.research_types.scientific_research.scientific_stage import ScientificStages
from data_to_paper.servers.custom_types import Citation


@dataclass
class GoalAndHypothesisProduct(ValueProduct):
    name: str = "Goal and Hypothesis"
    stage: ScientificStages = ScientificStages.GOAL
    value: str = None

    def _get_content_as_text(self, level: int, **kwargs):
        return self.value.replace('\n# ', '\n' + '#' * (level + 1) + ' ')


@dataclass
class MostSimilarPapersProduct(ValueProduct):
    name: str = "Papers Most Similar to our Research Goal"
    stage: ScientificStages = ScientificStages.ASSESS_NOVELTY
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
class NoveltyAssessmentProduct(ValueProduct):
    name: str = "Novelty Assessment"
    stage: ScientificStages = ScientificStages.ASSESS_NOVELTY
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
class HypothesisTestingPlanProduct(ValueProduct):
    name: str = 'Hypothesis Testing Plan'
    stage: ScientificStages = ScientificStages.PLAN
    value: Dict[str, str] = None

    def _get_content_as_markdown(self, level: int, **kwargs):
        s = ''
        for hypothesis, test in self.value.items():
            s += f'{"#" * (level + 1)} Hypothesis:\n{hypothesis}\n'
            s += f'{"#" * (level + 1)} Test:\n{test}\n\n'
        return s


@dataclass
class NoveltySummaryProduct(Product):
    name: str = 'Assessment of Research Goal Novelty'
    stage: ScientificStages = ScientificStages.ASSESS_NOVELTY
    most_similar_papers: MostSimilarPapersProduct = None
    novelty_assessment: NoveltyAssessmentProduct = None

    def _get_content_as_html(self, level: int, **kwargs):
        s = ''
        s += self.most_similar_papers.as_html(level + 1)
        s += '<br>'
        s += self.novelty_assessment.as_html(level + 1)
        return s
