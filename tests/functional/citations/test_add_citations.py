from _pytest.fixtures import fixture

from scientistgpt.conversation.conversation import OPENAI_SERVER_CALLER
from scientistgpt.gpt_interactors.citation_adding.call_crossref import CROSSREF_SERVER_CALLER
from scientistgpt.gpt_interactors.step_by_step.add_citations import AddCitationReviewGPT
from scientistgpt.gpt_interactors.types import Products

SECTIONS_TO_ADD_CITATIONS_TO = ['introduction']


@fixture
def products():
    return Products(
        research_goal="Find the distance to the moon.",
        results_summary="The distance to the moon is 384,400 km.",
        paper_sections={'title': "\\title{The distance to the moon} ",
                        'abstract': "\\begin{abstract} The distance to the moon is 384,400 km. "
                                    "This is a very long sentence.\\end{abstract}",
                        'introduction': "\\section{Introduction} The distance to the moon is 384,400 km. "
                                        "This was studied using a specific telescope called the Hubble telescope,"
                                        " which was launched in 1990. "})


@OPENAI_SERVER_CALLER.record_or_replay()
@CROSSREF_SERVER_CALLER.record_or_replay()
def test_citation_gpt(products):
    for section_name in SECTIONS_TO_ADD_CITATIONS_TO:
        products.cited_paper_sections[section_name] = \
            AddCitationReviewGPT(products=products, section_name=section_name).rewrite_section_with_citations()

    # check that we get the output with additional citations
    assert "\\cite{" in products.cited_paper_sections['introduction'][0]
