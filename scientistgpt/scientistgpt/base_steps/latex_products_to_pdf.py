from dataclasses import dataclass
from typing import Dict, Set

from scientistgpt.latex import save_latex_and_compile_to_pdf
from scientistgpt.servers.crossref import CrossrefCitation
from scientistgpt.latex.latex_to_pdf import clean_latex

from .base_products_to_file import BaseFileProducer

APPENDIX_TEMPLATE = r"""
\clearpage
\appendix
@@@appendix@@@
"""

CITATION_TEMPLATE = r"""
\bibliographystyle{unsrt}
\bibliography{citations}
"""

TEMPLATE_END = r"""
\end{document}"""

SECTION_NUMBERING = False
TABLE_TILDE = False


@dataclass
class BaseLatexToPDF(BaseFileProducer):
    """
    Allows creating a pdf based on a tex template whose sections are populated from the Products.
    """

    paper_template_filepath: str = None  # full path to the template file ending in .tex
    "The name of the file that holds the template for the paper."

    # output:
    _has_references: bool = False
    latex_paper: str = None

    @staticmethod
    def wrap_with_lstlisting(paragraph):
        return "\\begin{lstlisting}[language=TeX]\n" + paragraph + "\n\\end{lstlisting}"

    def get_raw_paper_template(self) -> str:
        """
        Load the bare, unmodified, template file.
        """
        with open(self.paper_template_filepath, 'r') as f:
            return f.read()

    def get_modified_paper_template(self) -> str:
        template = self.get_raw_paper_template()
        if self._has_references:
            template = template.replace(TEMPLATE_END, CITATION_TEMPLATE + TEMPLATE_END)
        return template

    def add_preamble(self, paper: str) -> str:
        """
        Return the preamble of the latex paper.
        """
        return '' + paper

    def _assemble_paper(self, sections):
        """
        Build the latex paper from the given sections.
        """
        paper = self.get_modified_paper_template()
        paper = self.add_preamble(paper)
        for section_name, section_content in sections.items():
            section_content = self._style_section(section_content)
            paper = paper.replace(f'@@@{section_name}@@@', section_content)
        return paper

    @staticmethod
    def _style_section(section: str) -> str:
        """
        Style the paper.
        """
        if not SECTION_NUMBERING:
            section = section.replace(r'\section', r'\section*').replace(r'\subsection', r'\subsection*')
        if not TABLE_TILDE:
            section = section.replace(r'Table\textasciitilde', r'Table ')
        return section

    def get_paper_section_names(self):
        return self.get_raw_paper_template().split('@@@')[1::2]

    def _choose_sections_to_add_to_paper_and_collect_references(self) -> (Dict[str, str], Set[CrossrefCitation]):
        """
        Return the content corresponding to each section in the tex template.
        Also return all the references cited.
        """
        pass

    def _save_latex_and_compile_to_pdf(self, references: Set[CrossrefCitation]):
        """
        Save the latex paper to .tex file and compile to pdf file.
        """
        clean_paper = clean_latex(self.latex_paper)
        save_latex_and_compile_to_pdf(clean_paper, self.output_file_stem, str(self.output_directory), references)

    def assemble_compile_paper(self):
        sections, references = self._choose_sections_to_add_to_paper_and_collect_references()
        self._has_references = bool(references)
        self.latex_paper = self._assemble_paper(sections)
        self._save_latex_and_compile_to_pdf(references)


@dataclass
class BaseLatexToPDFWithAppendix(BaseLatexToPDF):
    """
    Allows creating a pdf based on a tex template whose sections are populated from the Products. Also allows adding
    an appendix to the paper.
    """

    def get_modified_paper_template(self) -> str:
        return super().get_modified_paper_template().replace(TEMPLATE_END, APPENDIX_TEMPLATE + TEMPLATE_END)

    def _create_appendix(self) -> str:
        """
        Create the appendix.
        """
        raise NotImplementedError

    def _choose_sections_to_add_to_paper_and_collect_references(self):
        """
        Chooses what sections to add to the paper.
        Start by choosing section with tables, then cited sections, then without both of those.
        If there are references we also collect them to a set.
        """
        sections, references = super()._choose_sections_to_add_to_paper_and_collect_references()
        sections['appendix'] = self._create_appendix()
        return sections, references
