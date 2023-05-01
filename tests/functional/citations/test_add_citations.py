import os
import pickle

from scientistgpt.gpt_interactors.step_by_step.add_citations import AddCitationReviewGPT

PRODUCTS_PICKLE_FILEPATH = "./products_pickle/vaccine_products_pickle.pkl"
SECTIONS_TO_ADD_CITATIONS_TO = ['introduction', 'discussion']


def test_citation_gpt():
    with open(PRODUCTS_PICKLE_FILEPATH, "rb") as f:
        products = pickle.load(f)

    section_with_citations, products.bibtex_citations = \
        AddCitationReviewGPT(products=products,
                             sections={section_name: products.paper_sections[section_name] for section_name in
                                       SECTIONS_TO_ADD_CITATIONS_TO}).rewrite_sections_with_citations()
    products.paper_sections.update(section_with_citations)

    # check that we get the output with additional citations
    assert "\\cite{" in products.paper_sections['introduction_with_citations']
    assert "\\cite{" in products.paper_sections['discussion_with_citations']
