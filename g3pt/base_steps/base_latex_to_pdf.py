from dataclasses import dataclass
from typing import Dict, Set

from g3pt.latex import save_latex_and_compile_to_pdf
from g3pt.servers.crossref import CrossrefCitation

from .assemble_to_file import BaseFileProducer

APPENDIX_TEMPLATE = r"""
\clearpage
\appendix
@@@appendix@@@
"""

CITATION_TEMPLATE = r"""
\bibliographystyle{apalike}
\bibliography{citations}
"""

TEMPLATE_END = r"""
\end{document}"""


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
            paper = paper.replace(f'@@@{section_name}@@@', section_content)
        return paper

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
        save_latex_and_compile_to_pdf(self.latex_paper, self.output_file_stem, self.output_folder, references)

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
