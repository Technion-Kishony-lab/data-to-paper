from dataclasses import dataclass
from typing import Tuple

from scientistgpt.projects.scientific_research.literature_search import LiteratureSearchReviewGPT
from scientistgpt.servers.chatgpt import OPENAI_SERVER_CALLER
from scientistgpt.servers.semantic_scholar import SEMANTIC_SCHOLAR_SERVER_CALLER
from scientistgpt.servers.types import Citation
from tests.functional.base_steps.utils import TestProductsReviewGPT


@dataclass
class TestLiteratureSearchReviewGPT(TestProductsReviewGPT, LiteratureSearchReviewGPT):
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
    assert len(lit_search) == 4
    refs0 = next(iter(lit_search.values()))
    assert len(refs0) == 25
    assert all(isinstance(r, Citation) for r in refs0)
