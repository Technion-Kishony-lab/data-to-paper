import os

from scientistgpt.conversation.conversation import OPENAI_SERVER_CALLER
from scientistgpt.gpt_interactors.citation_adding.call_crossref import CROSSREF_SERVER_CALLER
from scientistgpt.gpt_interactors.citation_adding.citations_gpt import CitationGPT


@OPENAI_SERVER_CALLER.record_or_replay()
@CROSSREF_SERVER_CALLER.record_or_replay()
def test_citation_gpt(tmpdir):
    # create a scientific mentor with some random scientific products to test the paper author
    # pre_paper_conversation population
    section = """
\\section{Introduction}

The COVID-19 pandemic has led to a global health crisis that has affected millions of people around the \
world \\cite{some citation}. Vaccination is widely recognized as one of the most effective tools to control the \
spread of the virus and to reduce mortality. The Pfizer BioNTech (BNT162b2) COVID-19 vaccine has been authorized \
for emergency use in many countries, including Israel, where it has been administered to millions of people.

While the vaccine has been proven to be highly effective in preventing COVID-19 infections, there have been concerns \
regarding the safety profile of the vaccine. Reports of side effects following the administration of the vaccine \
have led to questions regarding the potential risks associated with the vaccine. 

In this study, we aimed to explore the differences in side effects across different portions of the \
Pfizer BioNTech (BNT162b2) COVID-19 vaccine. Specifically, we investigated the frequency and severity of side effects, \
unique side effects associated with specific portion numbers, and the onset and duration times of side effects \
across different portion numbers.

The research questions we aimed to address in this study are:
\\begin{enumerate}
    \\item Are there differences in the frequency and severity of side effects across different portion numbers?
    \\item Are there unique side effects associated with specific portion numbers?
    \\item How do the onset times and durations of side effects vary across portion numbers? 
    \\item Are there any trends or patterns in the occurrence of side effects across increasing or decreasing portion numbers?
\\end{enumerate}

To answer these questions, we analyzed the data on side effect reports submitted by medical staff in Israel following \
the administration of the Pfizer BioNTech (BNT162b2) COVID-19 vaccine. We used suitable data analysis and \
visualization tools to provide insights into the differences in side effect profiles across different portions of \
the vaccine.
    """
    citation_adder = CitationGPT(section=section)
    os.chdir(tmpdir)
    updated_section, all_citations_bibtexes = citation_adder.rewrite_section_with_citations()

    # check that we get the output with additional citations
    assert "\\cite{" in updated_section
