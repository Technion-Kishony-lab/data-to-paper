from dataclasses import dataclass
from typing import Tuple, Collection, Optional

from data_to_paper.base_steps import BaseLiteratureSearchReviewGPT
from data_to_paper.research_types.hypothesis_testing.cast import ScientificAgent
from data_to_paper.research_types.hypothesis_testing.scientific_products import ScientificProducts


@dataclass
class GoalLiteratureSearchReviewGPT(BaseLiteratureSearchReviewGPT):
    products: ScientificProducts = None
    requested_keys: Collection[str] = ('dataset', 'questions', )
    background_product_fields: Tuple[str, ...] = ('data_file_descriptions_no_headers', 'research_goal')
    conversation_name: str = 'Literature Search for Goal'
    is_new_conversation: bool = None
    goal_noun: str = 'literature search queries'
    goal_verb: str = 'write'
    assistant_agent: ScientificAgent = ScientificAgent.Performer
    user_agent: ScientificAgent = ScientificAgent.CitationExpert


@dataclass
class WritingLiteratureSearchReviewGPT(GoalLiteratureSearchReviewGPT):
    requested_keys: Collection[str] = ('background', 'dataset', 'methods', 'results')
    background_product_fields: Tuple[str, ...] = ('data_file_descriptions_no_headers', 'research_goal',
                                                  'hypothesis_testing_plan', 'title_and_abstract')
    conversation_name: str = 'Literature Search for Writing'

    def get_abstract(self) -> Optional[str]:
        return self.products.get_abstract()

    def get_title(self) -> Optional[str]:
        return self.products.get_title()
