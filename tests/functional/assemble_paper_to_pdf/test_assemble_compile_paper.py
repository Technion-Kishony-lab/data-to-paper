import os
from unittest import mock

from pytest import fixture

from data_to_paper.research_types.hypothesis_testing.produce_pdf_step import ProduceScientificPaperPDFWithAppendix
from data_to_paper.research_types.hypothesis_testing.scientific_products import ScientificProducts
from data_to_paper.code_and_output_files.output_file_requirements import OutputFileRequirementsToFileToContent
from data_to_paper.servers.crossref import CrossrefCitation

introduction_citation = {CrossrefCitation({
    "title": "Extended reporting guidance for vaccine effectiveness studies for variants of concern for COVID-19",
    "first_author_family": "Linkins",
    "authors": "Lori-Ann Linkins and Alfonso Iorio and Julian Little and John Lavis",
    "journal": "Vaccine",
    "doi": "10.1016/j.vaccine.2022.04.005",
    "type": "journal-article",
    "year": 2022,
}),
}

introduction_citation_id = next(iter(introduction_citation)).bibtex_id


@fixture()
def code_and_output():
    code_and_output = mock.Mock()
    # return value for function get_created_content_files_to_pretty_contents:
    code_and_output.created_files = OutputFileRequirementsToFileToContent()
    code_and_output.get_created_content_files_to_pretty_contents.return_value = {
        'table_1.tex': """\\begin{table}
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
"""
    }
    code_and_output.to_latex.return_value = "Nice code here"
    return code_and_output


@fixture()
def products(code_and_output):
    return ScientificProducts(
        paper_sections_and_optional_citations={'title': ('\\title{content of title}', set()),
                                               'abstract': (
                                               '\\begin{abstract}content of abstract\\end{abstract}', set()),
                                               'introduction': ('\\section{Introduction}This is the intro with citation'
                                                                '\\cite{' + introduction_citation_id + '}',
                                                                introduction_citation),
                                               'methods': ('\\section{Methods}{content of method}', set()),
                                               'results': ('\\section{Results}{content of results\n\n'
                                                           '2 + 3 is \\num{2+3, "triviality"}', set()),
                                               'discussion': ('\\section{Discussion}{content of discussion}', set()),
                                               'conclusion': ('\\section{Conclusion}{content of conclusion}', set()), },
        codes_and_outputs={'data_to_latex': code_and_output},
    )


def test_paper_assembler_compiler_gpt(tmpdir, products):
    paper_assembler_compiler = ProduceScientificPaperPDFWithAppendix(
        products=products,
        output_directory=tmpdir,
        output_filename='output.pdf',
        paper_section_names=['title', 'abstract', 'introduction', 'results', 'discussion', 'methods'],
    )

    latex_paper = paper_assembler_compiler.assemble_compile_paper()

    assert 'content of title' in latex_paper
    assert r'\hypertarget{results0}{}}2+3 = 5' in latex_paper
    assert r'2 + 3 is \hyperlink{results0}{5}' in latex_paper
    assert os.path.exists(os.path.join(tmpdir, paper_assembler_compiler.output_file_stem + '.tex'))
    assert os.path.exists(os.path.join(tmpdir, paper_assembler_compiler.output_file_stem + '.pdf'))
