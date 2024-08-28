import os
from copy import copy

import pandas as pd
from pathlib import Path
from pytest import fixture

from data_to_paper.code_and_output_files.code_and_output import CodeAndOutput
from data_to_paper.research_types.hypothesis_testing.coding.analysis.coding import \
    DataFramePickleContentOutputFileRequirement
from data_to_paper.research_types.hypothesis_testing.coding.displayitems.coding import \
    TexDisplayitemContentOutputFileRequirement
from data_to_paper.research_types.hypothesis_testing.produce_pdf_step import ProduceScientificPaperPDFWithAppendix
from data_to_paper.research_types.hypothesis_testing.scientific_products import ScientificProducts
from data_to_paper.code_and_output_files.output_file_requirements import OutputFileRequirementsToFileToContent
from data_to_paper.run_gpt_code.overrides.dataframes.df_with_attrs import ListInfoDataFrame
from data_to_paper.run_gpt_code.overrides.pvalue import PValue
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


analysis_code = r"""
import pandas as pd

## Table df_desc_stat:
df_desc_stat = ...
caption = ...
df_to_latex(df_desc_stat, 'df_desc_stat', caption=caption)

## Figure df_coefs:
df_coefs = ...
caption = ...
df_to_figure(df_coefs, 'df_coefs', caption=caption)
"""

displayitems_code = r"""
# IMPORT
import pandas as pd
from my_utils import df_to_latex, df_to_figure, is_str_in_df, split_mapping, AbbrToNameDef

# Process df_desc_stat
df_desc_stat = pd.read_pickle('df_desc_stat.pkl')
df_to_latex(
    df_desc_stat, 'df_desc_stat_formatted'
    caption=..., 
    note=...,
    glossary=...)

# Process df_coefs
df_coefs = pd.read_pickle('df_coefs.pkl')
df_to_figure(
    df_coefs, 'df_coefs_formatted'
    caption=...,
    note=...,
    glossary=...)
"""

provided_code = r"""
def df_to_latex(...):
    pass
"""


@fixture()
def code_and_outputs():
    df_desc_stat_0 = pd.DataFrame({'apl': [1, 2], 'ban': [4, 5]}, index=['mean', 'std'])
    df_desc_stat_1 = ListInfoDataFrame.from_prior_df(
        df_desc_stat_0,
        extra_info=('df_to_latex', df_desc_stat_0, 'df_desc_stat', dict())
    )
    df_desc_stat_1r = copy(df_desc_stat_1)
    df_desc_stat_1r.columns = ['apple', 'banana']
    df_desc_stat_2 = ListInfoDataFrame.from_prior_df(
        df_desc_stat_1r,
        extra_info=('df_to_latex', df_desc_stat_1r, 'df_desc_stat_formatted', {'caption': 'Caption', 'note': 'Note'})
    )

    df_coefs_0 = pd.DataFrame({'coef': [1.23456789, 2.1], 'p': [PValue(0.0001), PValue(0.001)]}, index=['a', 'b'])
    df_coefs_1 = ListInfoDataFrame.from_prior_df(
        df_coefs_0,
        extra_info=('df_to_figure', df_coefs_0, 'df_coefs', {'y': 'coef', 'y_pvalue': 'p'})
    )
    df_coefs_1r = copy(df_coefs_1)
    df_coefs_1r.index = ['apple', 'banana']
    df_coefs_2 = ListInfoDataFrame.from_prior_df(
        df_coefs_1r,
        extra_info=('df_to_figure', df_coefs_1r, 'df_coefs_formatted',
                    {'y': 'coef', 'y_pvalue': 'p', 'caption': 'Caption', 'note': 'Note'})
    )
    analysis_code_and_output = CodeAndOutput(
        name='Data Analysis',
        code=analysis_code,
        provided_code=provided_code,
        code_explanation="This code creates the data analysis tables and figures.",
        created_files=OutputFileRequirementsToFileToContent({
            DataFramePickleContentOutputFileRequirement('df_*.pkl', minimal_count=1):
                {'df_desc_stat.pkl': df_desc_stat_1,
                 'df_coefs.pkl': df_coefs_1},
        })
    )

    displayitems_code_and_output = CodeAndOutput(
        name='Create Latex',
        code=displayitems_code,
        provided_code=provided_code,
        code_explanation="This code creates the latex tables and figures.",
        created_files=OutputFileRequirementsToFileToContent({
            TexDisplayitemContentOutputFileRequirement('df_*_formatted.pkl', minimal_count=1):
                {'df_desc_stat_formatted.pkl': df_desc_stat_2,
                 'df_coefs_formatted.pkl': df_coefs_2},
        })
    )

    return {
        'data_analysis': analysis_code_and_output,
        'data_to_latex': displayitems_code_and_output,
    }

results = r"""
\section{Results}
In Table \ref{table:df-desc-stat-formatted} we see that \hyperlink{A0b}{4} + \hyperlink{A1b}{5} 
is \num{\hyperlink{A0b}{4} + \hyperlink{A1b}{5}, "the sum of two numbers"}.
In Figure \ref{figure:df-coefs-formatted}, we see that the coefficient for apples is \hyperlink{B0a}{1.235}.
"""

@fixture()
def products(code_and_outputs):
    return ScientificProducts(
        paper_sections_and_optional_citations={'title': ('\\title{content of title}', set()),
                                               'abstract': (
                                               '\\begin{abstract}content of abstract\\end{abstract}', set()),
                                               'introduction': ('\\section{Introduction}This is the intro with citation'
                                                                '\\cite{' + introduction_citation_id + '}',
                                                                introduction_citation),
                                               'methods': ('\\section{Methods}{content of method}', set()),
                                               'results': (results, set()),
                                               'discussion': ('\\section{Discussion}{content of discussion}', set()),
                                               'conclusion': ('\\section{Conclusion}{content of conclusion}', set()), },
        codes_and_outputs=code_and_outputs,
    )


def test_paper_assembler_compiler_gpt(tmpdir, products):
    # to get the pdf:
    # current_file_path = Path(os.path.abspath(__file__))
    # tmpdir = current_file_path.parent / 'temp'

    # create a simple df_coefs.png graphics file in the tmpdir:
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [1, 2, 3])
    plt.savefig(os.path.join(tmpdir, 'df_coefs_formatted.png'))

    paper_assembler_compiler = ProduceScientificPaperPDFWithAppendix(
        products=products,
        output_directory=tmpdir,
        output_filename='output.pdf',
        paper_section_names=['title', 'abstract', 'introduction', 'results', 'discussion', 'methods'],
        figures_folder=Path(tmpdir),
    )
    latex_paper = paper_assembler_compiler.assemble_compile_paper()

    # \num:
    assert 'content of title' in latex_paper
    assert r'\hypertarget{results0}{}\hyperlink{A0b}{4} + \hyperlink{A1b}{5} = 9' in latex_paper
    assert r'\hyperlink{results0}{9}' in latex_paper

    # reference to table
    assert r'\raisebox{2ex}{\hypertarget{A0b}{}}4' in latex_paper
    assert latex_paper.count('hypertarget{A0b}') == 1

    # reference to figure (points to latex sup mat):
    assert r'"apple",(*@\raisebox{2ex}{\hypertarget{B0a}{}}@*)1.235' in latex_paper
    assert latex_paper.count('hypertarget{B0a}') == 1

    # latex sup mat point to their source file:
    assert r'\subsubsection*{\hyperlink{file-df-coefs-pkl}{df\_coefs\_formatted.pkl}}' in latex_paper
    assert r'\end{codeoutput}' +'\n' + '\hypertarget{file-df-coefs-pkl}{}' in latex_paper

    # output of data analysis step point to code line:
    assert r'\subsubsection*{\hyperlink{code-df-desc-stat-pkl}{df\_desc\_stat.pkl}}' in latex_paper
    assert r'(*@\raisebox{2ex}{\hypertarget{code-df-desc-stat-pkl}{}}@*)## Table df_desc_stat:' in latex_paper

    assert os.path.exists(os.path.join(tmpdir, paper_assembler_compiler.output_file_stem + '.tex'))
    assert os.path.exists(os.path.join(tmpdir, paper_assembler_compiler.output_file_stem + '.pdf'))
