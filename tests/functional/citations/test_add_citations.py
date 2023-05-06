from _pytest.fixtures import fixture

from scientistgpt.projects.scientific_research.scientific_products import ScientificProducts
from scientistgpt.servers.chatgpt import OPENAI_SERVER_CALLER
from scientistgpt.servers.crossref import CROSSREF_SERVER_CALLER
from scientistgpt.projects.scientific_research.add_citations import AddCitationReviewGPT

SECTIONS_TO_ADD_CITATIONS_TO = ['introduction']


@fixture
def products():
    return ScientificProducts(
        research_goal="Find the distance to the moon.",
        results_summary="The distance to the moon is 384,400 km.",
        paper_sections={'title': "\\title{The distance to the moon} ",
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
def test_citation_gpt(products):
    for section_name in SECTIONS_TO_ADD_CITATIONS_TO:
        products.cited_paper_sections[section_name] = \
            AddCitationReviewGPT(products=products, section_name=section_name).rewrite_section_with_citations()

    # check that we get the output with additional citations
    assert "\\cite{" in products.cited_paper_sections['introduction'][0]
