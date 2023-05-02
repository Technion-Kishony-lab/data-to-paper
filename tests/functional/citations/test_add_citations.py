import pickle

from scientistgpt.conversation.conversation import OPENAI_SERVER_CALLER
from scientistgpt.gpt_interactors.citation_adding.call_crossref import CROSSREF_SERVER_CALLER
from scientistgpt.gpt_interactors.step_by_step.add_citations import AddCitationReviewGPT

PRODUCTS_PICKLE_FILEPATH = "./products_pickle/vaccine_products_pickle.pkl"
SECTIONS_TO_ADD_CITATIONS_TO = ['introduction', 'discussion']


@OPENAI_SERVER_CALLER.record_or_replay()
@CROSSREF_SERVER_CALLER.record_or_replay()
def test_citation_gpt():
    with open(PRODUCTS_PICKLE_FILEPATH, "rb") as f:
        products = pickle.load(f)

    # add cited_paper_sections field to products
    products.cited_paper_sections = {}

    for section_name in SECTIONS_TO_ADD_CITATIONS_TO:
        products.cited_paper_sections[section_name] = \
            AddCitationReviewGPT(products=products, section_name=section_name).rewrite_section_with_citations()

    # check that we get the output with additional citations
    assert "\\cite{" in products.cited_paper_sections['introduction']
    assert "\\cite{" in products.cited_paper_sections['discussion']
