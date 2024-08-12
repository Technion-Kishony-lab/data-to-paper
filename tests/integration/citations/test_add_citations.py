from pytest import fixture

from data_to_paper.research_types.hypothesis_testing.product_types import GoalAndHypothesisProduct
from data_to_paper.research_types.hypothesis_testing.scientific_products import ScientificProducts
from data_to_paper.servers.llm_call import OPENAI_SERVER_CALLER
from data_to_paper.servers.crossref import CROSSREF_SERVER_CALLER
from data_to_paper.research_types.hypothesis_testing.add_citations import AddCitationReviewGPT

SECTIONS_TO_ADD_CITATIONS_TO = ['introduction']


@fixture
def products():
    return ScientificProducts(
        research_goal=GoalAndHypothesisProduct(value="Find the distance to the moon."),
        paper_sections_and_optional_citations={
            'title': "\\title{The distance to the moon} ",
            'abstract': "\\begin{abstract} The distance to the moon is 384,400 km. "
                        "This is a very long sentence.\\end{abstract}",
            'introduction': "\\section{Introduction} The distance to the moon is 384,400 km. "
                            "This was studied using a specific telescope called the Hubble telescope,"
                            " which was launched in 1990. "
                            "Some more interesting details that need references are:"
                            " This is one of the most important discoveries in astronomy, after the "
                            "discovery of the circumference of the earth. "
                            "In later years, the mission of nasa named Apollo 11 was launched to the moon."}
    )


@OPENAI_SERVER_CALLER.record_or_replay()
@CROSSREF_SERVER_CALLER.record_or_replay()
def test_citation_gpt(actions_and_conversations, products):
    for section_name in SECTIONS_TO_ADD_CITATIONS_TO:
        products.paper_sections_and_optional_citations[section_name] = \
            AddCitationReviewGPT(
                actions_and_conversations=actions_and_conversations,
                products=products, section_name=section_name).rewrite_section_with_citations()

    # check that we get the output with additional citations
    assert "\\cite{" in products.paper_sections_and_optional_citations['introduction'][0]
