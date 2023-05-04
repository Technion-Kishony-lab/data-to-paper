import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

from g3pt.gpt_interactors.step_by_step.latex_paper_compilation.get_template import get_paper_template, \
    get_paper_section_names
from g3pt.gpt_interactors.step_by_step.latex_paper_compilation.latex import save_latex_and_compile_to_pdf
from g3pt.gpt_interactors.types import Products


@dataclass
class PaperAssemblerCompiler:
    """
    Allows assembling the paper sections into tex file and compiling it with citations into a paper.
    """

    paper_filename: str = 'paper'
    """
    The name of the file that gpt code is instructed to save the results to.
    """
    bib_filename: str = 'citations.bib'
    """
    The name of the file that gpt code is instructed to save the bibliography to.
    """
    paper_template_filename: str = 'standard_paper.tex'
    """
    The name of the file that holds the template for the paper.
    """
    paper_template_with_citations_filename: str = 'standard_paper_with_citations.tex'
    """
    The name of the file that holds the template for the paper with citations.
    """

    output_directory: Optional[Union[str, Path]] = None

    products: Products = None

    should_compile_with_bib: bool = False

    latex_paper: str = None

    @property
    def latex_filename(self) -> str:
        return f'{self.paper_filename}.tex'

    @property
    def pdf_filename(self) -> str:
        return f'{self.paper_filename}.pdf'

    def _assemble_paper(self, sections):
        """
        Build the latex paper from the given sections.
        """
        if self.should_compile_with_bib:
            paper = get_paper_template(self.paper_template_with_citations_filename)
        else:
            paper = get_paper_template(self.paper_template_filename)

        for section_name in sections:
            paper = paper.replace(f'@@@{section_name}@@@', sections[section_name])

        return paper

    def _choose_sections_to_add_to_paper_and_collect_references(self):
        """
        Chooses what sections to add to the paper.
        Start by choosing section with tables, then cited sections, then without both of those.
        If there are references we also collect them to a set.
        """
        references = set()
        sections = {}
        for section_name in get_paper_section_names(self.paper_template_filename):
            if section_name in self.products.paper_sections_with_tables:
                sections[section_name] = self.products.paper_sections_with_tables[section_name]
                if section_name in self.products.cited_paper_sections:
                    references |= self.products.cited_paper_sections[section_name][1]
            elif section_name in self.products.cited_paper_sections:
                sections[section_name] = self.products.cited_paper_sections[section_name][0]
                references |= self.products.cited_paper_sections[section_name][1]
            else:
                sections[section_name] = self.products.paper_sections[section_name]

        return sections, references

    def _save_latex_and_compile_to_pdf(self):
        """
        Save the latex paper to .tex file and compile to pdf file.
        """
        save_latex_and_compile_to_pdf(self.latex_paper, self.paper_filename, self.output_directory,
                                      self.should_compile_with_bib)

    def _save_references_to_bib_file(self, references: set):
        """
        Save all the citations bibtexes to a .bib file in the output folder.
        """
        references_bibtex = [reference.create_bibtex() for reference in references]
        with open(os.path.join(self.output_directory, self.bib_filename), 'w') as f:
            f.write('\n\n'.join(references_bibtex))

    def assemble_compile_paper(self):
        sections, references = self._choose_sections_to_add_to_paper_and_collect_references()
        if references:
            self.should_compile_with_bib = True
            self._save_references_to_bib_file(references)
        self.latex_paper = self._assemble_paper(sections)
        self._save_latex_and_compile_to_pdf()
