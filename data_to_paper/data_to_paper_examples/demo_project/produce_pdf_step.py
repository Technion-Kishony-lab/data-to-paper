from dataclasses import dataclass
from typing import Dict

from data_to_paper.base_steps import BaseLatexToPDF

from products import DemoProducts


@dataclass
class ProduceDemoPaperPDF(BaseLatexToPDF):
    products: DemoProducts = None

    def _get_title(self) -> str:
        return self.products.paper_sections['title']

    def _get_abstract(self) -> str:
        return self.products.paper_sections['abstract']

    def _get_sections(self) -> Dict[str, str]:
        return {section_name: self.products.paper_sections[section_name]
                for section_name in self.paper_section_names}

    def _get_appendix(self):
        s = self.products.data_file_descriptions.to_latex()
        s += '\n\n' + self.products.code_and_output.to_latex()
        return s
