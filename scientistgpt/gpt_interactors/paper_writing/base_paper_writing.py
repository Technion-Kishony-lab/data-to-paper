import os
from abc import abstractmethod, ABC
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, Union

from scientistgpt.exceptions import ScientistGPTException
# from scientistgpt.gpt_interactors.citation_adding.citations_gpt import CitationGPT
from scientistgpt.gpt_interactors.converser_gpt import ConverserGPT
from scientistgpt.latex import save_latex_and_compile_to_pdf
from scientistgpt.utils import dedent_triple_quote_str


@dataclass
class FailedCreatingPaperSection(ScientistGPTException):
    section: str

    def __str__(self):
        return f'Failed to create the {self.section} section of the paper.'


@dataclass
class FailedCreatingPaper(ScientistGPTException):
    exception: Exception

    def __str__(self):
        return f'Failed to create the paper because of\n{self.exception}'


@dataclass
class PaperWritingGPT(ConverserGPT, ABC):
    """
    Base class for agents interacting with chatgpt to write a latex/pdf paper.

    Allows writing the paper section by section and assembling the sections into a paper.
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

    paper_sections: Dict[str, str] = field(default_factory=dict)

    latex_paper: str = None

    system_prompt: str = dedent_triple_quote_str("""
        You are a scientist capable of writing full-length, scientifically sound research papers.

        You should:
        1. Write every part of the paper in scientific language, in `.tex` format.
        2. Write the paper section by section.
        3. Write the paper in a way that is consistent with the scientific products provided to you.
        4. Do not cite any papers.
        """)

    @property
    def latex_filename(self) -> str:
        return f'{self.paper_filename}.tex'

    @property
    def pdf_filename(self) -> str:
        return f'{self.paper_filename}.pdf'

    @abstractmethod
    def _pre_populate_conversation(self):
        """
        Populate the conversation before starting to write the sections.
        """
        pass

    @abstractmethod
    def _get_paper_sections(self):
        """
        Fill all the paper sections in paper_sections
        Should raise FailedCreatingPaperSection if failed to create a section.
        """
        pass

    def _assemble_latex_paper_from_sections(self, should_compile_with_bib: bool = True):
        """
        Assemble the paper from the different sections.
        """
        # We replace each section with the corresponding content (sections are marked with @@@section_name@@@)
        if should_compile_with_bib:
            paper = self.paper_template_with_citations
        else:
            paper = self.paper_template
        for section_name, section_content in self.paper_sections.items():
            paper = paper.replace(f'@@@{section_name}@@@', section_content)
        self.latex_paper = paper

    def _save_latex_and_compile_to_pdf(self, should_compile_to_pdf: bool = True, should_compile_with_bib: bool = True):
        """
        Save the latex paper to .tex file and compile to pdf file.
        """
        # running from data folder, the output folder is one level up from the os.cwd() and inside 'output'
        # output_folder = os.path.join(os.getcwd(), '..', 'output')
        # if not os.path.exists(output_folder):
        #     raise Exception(f'Output folder {output_folder} does not exist.')
        save_latex_and_compile_to_pdf(self.latex_paper, self.paper_filename, self.output_directory,
                                      should_compile_with_bib, should_compile_to_pdf)

    def _save_references_to_bib_file(self, references: set):
        """
        Save all the citations bibtexes to a .bib file in the output folder.
        """
        with open(os.path.join(self.output_directory, self.bib_filename), 'w') as f:
            f.write('\n\n'.join(references))

    def write_paper(self, should_compile_to_pdf: bool = True, should_compile_with_bib: bool = True):
        self.initialize_conversation_if_needed()
        self._pre_populate_conversation()
        try:
            self._get_paper_sections()
        except FailedCreatingPaperSection as e:
            raise FailedCreatingPaper(e)
        # self._add_citations_to_paper()
        self._assemble_latex_paper_from_sections(should_compile_with_bib)
        self._save_latex_and_compile_to_pdf(should_compile_to_pdf, should_compile_with_bib)

    # def _add_citations_to_paper(self):
    #     """
    #     Add citations to all the relevant sections of the paper and add any necessary bibtex
    #     references to the .bib file.
    #     """
    #     all_references = set()
    #     for section_name, section_content in self.paper_sections.items():
    #         if section_name in ['title', 'abstract', 'results', 'methods', 'conclusion']:
    #             continue
    #         # self.paper_sections[section_name], references = \
    #             # CitationGPT(section=section_content).rewrite_section_with_citations()
    #         # all_references |= references
    #     self._save_references_to_bib_file(all_references)
