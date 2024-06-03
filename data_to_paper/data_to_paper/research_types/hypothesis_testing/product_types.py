from dataclasses import dataclass
from typing import List, Dict, Any

from data_to_paper.base_products.product import ValueProduct, Product
from data_to_paper.code_and_output_files.file_view_params import ViewPurpose
from data_to_paper.research_types.hypothesis_testing.scientific_stage import ScientificStage
from data_to_paper.servers.custom_types import Citation


@dataclass
class GoalAndHypothesisProduct(ValueProduct):
    name: str = "Goal and Hypothesis"
    stage: ScientificStage = ScientificStage.GOAL
    value: str = None

    def _get_content_as_formatted_text(self, level: int, view_purpose: ViewPurpose, **kwargs) -> str:
        return ('\n' + self.value).replace('\n# ', '\n' + '#' * (level + 1) + ' ').strip()


@dataclass
class MostSimilarPapersProduct(ValueProduct):
    name: str = "Papers Most Similar to our Research Goal"
    stage: ScientificStage = ScientificStage.ASSESS_NOVELTY
    value: List[Citation] = None

    def _get_citations(self, is_html=False):
        return '\n'.join(citation.pretty_repr(
            fields=('bibtex_id', 'title', 'journal_and_year', 'tldr'),
            is_html=is_html,
        ) for citation in self.value)

    def _get_content_as_formatted_text(self, level: int, view_purpose: ViewPurpose, **kwargs) -> str:
        return self._get_citations(is_html=False)

    def _get_content_as_html(self, level: int, **kwargs):
        return self._get_citations(is_html=True)


@dataclass
class NoveltyAssessmentProduct(ValueProduct):
    name: str = "Novelty Assessment"
    stage: ScientificStage = ScientificStage.ASSESS_NOVELTY
    value: Dict[str, Any] = None

    def _get_content_as_formatted_text(self, level: int, view_purpose: ViewPurpose, **kwargs) -> str:
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
    stage: ScientificStage = ScientificStage.PLAN
    value: Dict[str, Dict[str, str]] = None

    def _get_content_as_formatted_text(self, level: int, view_purpose: ViewPurpose, **kwargs) -> str:
        s = ''
        issues = self.value['ISSUES']
        hypotheses = self.value['HYPOTHESES']
        s += f'{"#" * (level + 1)} Statistical considerations:\n'
        for issue, description in issues.items():
            s += f'{"#" * (level + 2)} {issue}:\n{description}\n'

        s += '\n'
        s += f'{"#" * (level + 1)} Hypotheses:\n'
        for hypothesis, test in hypotheses.items():
            s += f'{"#" * (level + 2)} Hypothesis:\n{hypothesis}\n'
            s += f'{"#" * (level + 2)} Test:\n{test}\n\n'
        return s


@dataclass
class NoveltySummaryProduct(Product):
    name: str = 'Assessment of Research Goal Novelty'
    stage: ScientificStage = ScientificStage.ASSESS_NOVELTY
    most_similar_papers: MostSimilarPapersProduct = None
    novelty_assessment: NoveltyAssessmentProduct = None

    def is_valid(self):
        return self.most_similar_papers and self.novelty_assessment

    def _get_content_as_html(self, level: int, **kwargs):
        s = ''
        s += self.most_similar_papers.as_html(level + 1)
        s += '<br>'
        s += self.novelty_assessment.as_html(level + 1)
        return s
