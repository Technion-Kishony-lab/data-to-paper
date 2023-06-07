from dataclasses import dataclass

from pygments import highlight
from pygments.formatters.latex import LatexFormatter
from pygments.lexers import PythonLexer

from scientistgpt.base_steps import BaseLatexToPDF, BaseLatexToPDFWithAppendix
from scientistgpt.projects.scientific_research.scientific_products import ScientificProducts
from scientistgpt.run_gpt_code.types import CodeAndOutput
from scientistgpt.utils.text_formatting import wrap_python_code
from scientistgpt.utils.types import ListBasedSet


@dataclass
class ProduceScientificPaperPDF(BaseLatexToPDF):
    products: ScientificProducts = None

    def _choose_sections_to_add_to_paper_and_collect_references(self):
        """
        Chooses what sections to add to the paper.
        Start by choosing section with tables, then cited sections, then without both of those.
        If there are references we also collect them to a set.
        """
        references = ListBasedSet()
        sections = {}
        for section_name in self.get_paper_section_names():
            sections[section_name] = self.products.most_updated_paper_sections[section_name]
            if section_name in self.products.cited_paper_sections_and_citations:
                references |= self.products.cited_paper_sections_and_citations[section_name][1]  # 1 is the references

        return sections, references


@dataclass
class ProduceScientificPaperPDFWithAppendix(BaseLatexToPDFWithAppendix, ProduceScientificPaperPDF):
    latex_formatter: LatexFormatter = LatexFormatter(linenos=True, texcomments=False, mathescape=False,
                                                     verboptions=r"formatcom=\footnotesize")

    def __post_init__(self):
        BaseLatexToPDFWithAppendix.__post_init__(self)
        ProduceScientificPaperPDF.__post_init__(self)

    def _create_code_section(self, code_and_output: CodeAndOutput):
        """
        Create the code section.
        """
        section_name = code_and_output.name
        code = wrap_python_code(code_and_output.code)
        latex_code = highlight(code, PythonLexer(), self.latex_formatter)
        code_section = f"\\section{{{section_name}}} \\subsection{{Code}}" \
                       f"Performing the {section_name} carried out using the " \
                       "following custom code (created by ChatGPT):"
        code_section += '\n\n' + latex_code
        if code_and_output.code_explanation:
            code_section += "\\subsection{Code Description}"
            code_section += '\n\n' + code_and_output.code_explanation
        if code_and_output.output:
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

        for code_step in self.products.codes_and_outputs:
            code_and_output = self.products.codes_and_outputs[code_step]
            appendix += '\n\n' + self._create_code_section(code_and_output)
        return appendix
