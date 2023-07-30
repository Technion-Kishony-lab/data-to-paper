from dataclasses import dataclass
from typing import List, Dict

from data_to_paper.base_steps import BaseLatexToPDFWithAppendix
from data_to_paper.servers.crossref import CrossrefCitation

from products import DemoProducts


@dataclass
class ProduceDemoPaperPDF(BaseLatexToPDFWithAppendix):
    products: DemoProducts = None

    def _choose_sections_to_add_to_paper_and_collect_references(self) -> (Dict[str, str], List[CrossrefCitation]):
        sections, references = super()._choose_sections_to_add_to_paper_and_collect_references()
        added_sections = {section_name: self.products.paper_sections[section_name]
                          for section_name in self.paper_section_names}
        return {**sections, **added_sections}, references

    def _create_appendix(self):
        s = self.products.data_file_descriptions.to_latex()
        s += '\n\n' + self.products.code_and_output.to_latex()
        return s
