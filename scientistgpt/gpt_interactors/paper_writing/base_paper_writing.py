import os
from abc import abstractmethod, ABC
from dataclasses import dataclass, field
from typing import Dict

from scientistgpt.gpt_interactors.converser_gpt import ConverserGPT
from scientistgpt.latex import save_latex_and_compile_to_pdf
from scientistgpt.utils import dedent_triple_quote_str


@dataclass
class PaperWritingGPT(ConverserGPT, ABC):
    """
    Base class for agents interacting with chatgpt to write a latex/pdf paper.

    Allows writing the paper section by section and assembling the sections into a paper.
    """

    agent: str = 'Author'

    paper_filename: str = 'paper'
    """
    The name of the file that gpt code is instructed to save the results to.
    """

    paper_template_filename: str = 'standard_paper.tex'
    """
    The name of the file that holds the template for the paper.
    """

    paper_sections: Dict[str, str] = field(default_factory=dict)

    latex_paper: str = None

    system_prompt: str = dedent_triple_quote_str("""
        You are a scientist capable of writing full-length, scientifically sound research papers.

        Your should:
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

    @property
    def paper_template_path(self) -> str:
        return os.path.join(os.path.dirname(__file__), f'templates/{self.paper_template_filename}')

    @property
    def paper_template(self) -> str:
        """
        Load the specified template file.
        """
        with open(self.paper_template_path, 'r') as f:
            return f.read()

    @property
    def paper_section_names(self):
        """
        Get the sections of the paper from the template.
        Sections are flaked as: @@@section_name@@@
        """
        return self.paper_template.split('@@@')[1::2]

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
        """
        pass

    def _assemble_latex_paper_from_sections(self):
        """
        Assemble the paper from the different sections.
        """
        # We replace each section with the corresponding content (sections are marked with @@@section_name@@@)
        paper = self.paper_template
        for section_name, section_content in self.paper_sections.items():
            paper = paper.replace(f'@@@{section_name}@@@', section_content)
        self.latex_paper = paper

    def _save_latex_and_compile_to_pdf(self, should_compile_to_pdf: bool = True):
        """
        Save the latex paper to .tex file and compile to pdf file.
        """
        save_latex_and_compile_to_pdf(self.latex_paper, self.paper_filename, should_compile_to_pdf)

    def write_paper(self, should_compile_to_pdf: bool = True):
        self.initialize_conversation_if_needed()
        self._pre_populate_conversation()
        self._get_paper_sections()
        self._assemble_latex_paper_from_sections()
        self._save_latex_and_compile_to_pdf(should_compile_to_pdf)
