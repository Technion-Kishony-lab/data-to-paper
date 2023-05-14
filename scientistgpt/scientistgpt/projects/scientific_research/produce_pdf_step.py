from dataclasses import dataclass

from pygments import highlight
from pygments.formatters.latex import LatexFormatter
from pygments.lexers import PythonLexer

from scientistgpt.base_steps import BaseLatexToPDF, BaseLatexToPDFWithAppendix
from scientistgpt.projects.scientific_research.scientific_products import ScientificProducts, \
    get_from_most_updated_paper_sections
from scientistgpt.utils.text_utils import wrap_python_code


@dataclass
class ProduceScientificPaperPDF(BaseLatexToPDF):
    products: ScientificProducts = None

    def _choose_sections_to_add_to_paper_and_collect_references(self):
        """
        Chooses what sections to add to the paper.
        Start by choosing section with tables, then cited sections, then without both of those.
        If there are references we also collect them to a set.
        """
        references = set()
        sections = {}
        for section_name in self.get_paper_section_names():
            sections[section_name] = get_from_most_updated_paper_sections(self.products, section_name)
            if section_name in self.products.cited_paper_sections:
                references |= self.products.cited_paper_sections[section_name][1]  # 1 is the references set

        return sections, references


@dataclass
class ProduceScientificPaperPDFWithAppendix(BaseLatexToPDFWithAppendix, ProduceScientificPaperPDF):
    latex_formatter: LatexFormatter = LatexFormatter(linenos=True, texcomments=True, mathescape=True,
                                                     verboptions=r"formatcom=\footnotesize")

    def _create_code_section(self):
        """
        Create the code section.
        """
        code_and_output = self.products.code_and_output
        code = wrap_python_code(code_and_output.code)
        latex_code = highlight(code, PythonLexer(), self.latex_formatter)
        code_section = "\\section{Python Analysis Code} \\label{sec:code} \\subsection{Code}" \
                       "Data analysis was carried out using the " \
                       "following custom code (created by ChatGPT):"
        code_section += '\n\n' + latex_code
        code_section += "\\subsection{Code Description}"
        code_section += '\n\n' + code_and_output.explanation
        code_section += '\n\n' + "\\subsection{Code Output}"
        code_section += '\n\n' + self.wrap_with_lstlisting(code_and_output.output)
        return code_section

    def _create_data_description_section(self):
        """
        Create the data description section.
        """
        data_file_descriptions = self.products.data_file_descriptions
        data_description_section = "\\section{Data Description} \\label{sec:data_description} Here is the data " \
                                   "description, as provided by the user:"""
        data_description_section += '\n\n' + self.wrap_with_lstlisting(
            data_file_descriptions.pretty_repr(num_lines=0))
        return data_description_section

    def add_preamble(self, paper: str) -> str:
        return self.latex_formatter.get_style_defs() + paper

    def _create_appendix(self):
        """
        Create the appendix.
        """
        appendix = self._create_data_description_section()
        appendix += '\n\n' + self._create_code_section()
        return appendix
