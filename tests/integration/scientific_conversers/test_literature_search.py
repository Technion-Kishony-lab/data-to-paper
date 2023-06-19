from dataclasses import dataclass
from typing import Tuple

from data_to_paper.projects.scientific_research.literature_search import WritingLiteratureSearchReviewGPT
from data_to_paper.servers.chatgpt import OPENAI_SERVER_CALLER
from data_to_paper.servers.semantic_scholar import SEMANTIC_SCHOLAR_SERVER_CALLER
from data_to_paper.servers.types import Citation
from tests.functional.base_steps.utils import TestProductsReviewGPT


@dataclass
class TestLiteratureSearchReviewGPT(TestProductsReviewGPT, WritingLiteratureSearchReviewGPT):
    background_product_fields: Tuple[str, ...] = ()
    requested_keys: Tuple[str, ...] = ('background', 'results')
    step: str = 'test'


response = {
    "background": ["COVID-19 spread", "COVID-19 vaccine efficacy"],
    "results": ["COVID-19 vaccine efficacy over time", "COVID-19 vaccine efficacy waning"]
}


@SEMANTIC_SCHOLAR_SERVER_CALLER.record_or_replay()
def test_literature_search():
    searcher = TestLiteratureSearchReviewGPT()
    with OPENAI_SERVER_CALLER.mock([str(response)], record_more_if_needed=False):
        lit_search = searcher.get_literature_search()
    assert lit_search.scopes_to_queries_to_citations.keys() == {'background', 'results'}
    assert lit_search.scopes_to_queries_to_citations['background'].keys() == {'COVID-19 spread', 'COVID-19 vaccine efficacy'}
    assert lit_search.scopes_to_queries_to_citations['results'].keys() == {'COVID-19 vaccine efficacy over time', 'COVID-19 vaccine efficacy waning'}
    refs0 = next(iter(lit_search.scopes_to_queries_to_citations['results'].values()))
    assert len(refs0) > 0
    assert all(isinstance(r, Citation) for r in refs0)
