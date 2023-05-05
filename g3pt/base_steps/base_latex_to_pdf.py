import os
from dataclasses import dataclass
from typing import Dict, Set

from g3pt.base_steps.assemble_to_file import BaseFileProducer
from g3pt.latex.latex_to_pdf import BIB_FILENAME
from g3pt.projects.scientific_research.latex_paper_compilation.get_template import get_paper_template
from g3pt.latex import save_latex_and_compile_to_pdf
from g3pt.servers.crossref import CrossrefCitation


CITATION_TEMPLATE = r"""
\bibliographystyle{apalike}
\bibliography{citations}

\end{document}
"""

TEMPLATE_END = r"""
\end{document}
"""


@dataclass
class BaseLatexToPDF(BaseFileProducer):
    """
    Allows creating a pdf based on a tex template whose sections are populated from the Products.
    """

    paper_template_filepath: str = 'standard_paper.tex'
    "The name of the file that holds the template for the paper."

    # output:
    _has_references: bool = False
    latex_paper: str = None

    def get_paper_template(self) -> str:
        template = get_paper_template(self.paper_template_filepath)
        if self._has_references:
            template = template.replace(TEMPLATE_END, CITATION_TEMPLATE)
        return template

    def _assemble_paper(self, sections):
        """
        Build the latex paper from the given sections.
        """
        paper = self.get_paper_template()
        for section_name, section_content in sections.items():
            paper = paper.replace(f'@@@{section_name}@@@', section_content)
        return paper

    def get_paper_section_names(self):
        return self.get_paper_template().split('@@@')[1::2]

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
