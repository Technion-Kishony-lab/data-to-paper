import os
from dataclasses import dataclass

from _pytest.fixtures import fixture

from scientistgpt.base_steps.types import DataFileDescription, DataFileDescriptions
from scientistgpt.projects.scientific_research.get_template import get_paper_template_path
from scientistgpt.projects.scientific_research.scientific_products import ScientificProducts
from scientistgpt.projects.scientific_research.steps import ProduceScientificPaperPDFWithAppendix
from scientistgpt.run_gpt_code.types import CodeAndOutput
from scientistgpt.servers.crossref import CrossrefCitation


@dataclass(frozen=True)
class TestDataFileDescription(DataFileDescription):
    file_path: str  # relative to the data directory.  should normally just be the file name
    description: str  # a user provided description of the file

    def get_file_header(self, num_lines: int = 4):
        """
        Return the first `num_lines` lines of the file.
        """
        return """
        This is the first line of the file.
        This is the second line of the file.
        This is the third line of the file.
        This is the fourth line of the file.
        This is the fifth line of the file.
        """


INTRODUCTION_CITATION = {CrossrefCitation({
    "title": "Extended reporting guidance for vaccine effectiveness studies for variants of concern for COVID-19",
    "first_author_family": "Linkins",
    "authors": "Lori-Ann Linkins and Alfonso Iorio and Julian Little and John Lavis",
    "journal": "Vaccine",
    "doi": "10.1016/j.vaccine.2022.04.005",
    "type": "journal-article",
    "year": 2022,
}),
}

CODE = """
def fast_recursive_fibonacci(n):
    # just to see if we can also see comments in code and also to test if the line is too long to fit in the paper
    if n <= 1:
        return n
    else:
        return fast_recursive_fibonacci(n - 1) + fast_recursive_fibonacci(n - 2)

results = []
for i in range(20):
    results.append(fast_recursive_fibonacci(i))
with open('output.txt', 'w') as f:
    f.write(', '.join([str(x) for x in results]))
"""
OUTPUT = "0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987, 1597, 2584, 4181."
EXPLANATION = "This is the explanation of the code:" \
              "The code is a recursive function that calculates the fibonacci sequence." \
              "The output is a list of the first 20 fibonacci numbers."

INTRODUCTION_CITATION_ID = next(iter(INTRODUCTION_CITATION)).get_bibtex_id()
DATA_FILE_DESCRIPTION = DataFileDescriptions([TestDataFileDescription('data_file_1', 'this is important data')])


@fixture
def products():
    return ScientificProducts(
        data_file_descriptions=DATA_FILE_DESCRIPTION,
        paper_sections={'title': '\\title{content of title}',
                        'abstract': '\\begin{abstract}content of abstract\\end{abstract}',
                        'introduction': '\\section{Introduction}{content of introduction}',
                        'methods': '\\section{Methods}{content of method}',
                        'results': '\\section{Results}{content of results}',
                        'discussion': '\\section{Discussion}{content of discussion}',
                        'conclusion': '\\section{Conclusion}{content of conclusion}', },
        cited_paper_sections={'introduction': ('\\section{Introduction}'
                                               'This is the intro with citation'
                                               '\\cite{' + INTRODUCTION_CITATION_ID + '}', INTRODUCTION_CITATION)},
        paper_sections_with_tables={'results': """
                                            \\section{Results}
                                            This is the results with table:
                                            \\begin{table}
                                            \\centering
                                            \\begin{tabular}{ *{3}{c} }
                                            \\toprule
                                            Temperature ($^{\\circ}$F) & Average melting time (s) & 95\\% CI \\\\
                                            \\midrule
                                            130 & 38.75 & (28.54, 48.96) \\\\
                                            140 & 21.31 & (9.94, 32.69)  \\\\
                                            150 & 15.36 & (3.61, 27.11)  \\\\
                                            \\bottomrule
                                            \\end{tabular}
                                            \\caption{The means and 95\\% confidence intervals for each temperature.}
                                            \\end{table}
                                            """},
        code_and_output=CodeAndOutput(code=CODE, output=OUTPUT, output_file='output.txt', explanation=EXPLANATION),
    )


def test_paper_appendix_creator(tmpdir, products):
    paper_producer = ProduceScientificPaperPDFWithAppendix(
        products=products,
        output_file_path=tmpdir / 'output.pdf',
        paper_template_filepath=get_paper_template_path('standard_paper.tex'),
    )
    paper_producer.assemble_compile_paper()
    os.chdir(tmpdir)
    assert '@@@appendix@@@' not in paper_producer.latex_paper
    assert os.path.exists(paper_producer.output_file_stem + '.tex')
    assert os.path.exists(paper_producer.output_file_stem + '.pdf')
