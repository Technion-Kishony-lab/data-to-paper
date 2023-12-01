from dataclasses import dataclass
from typing import Dict, List

from data_to_paper.base_steps import BaseLatexToPDF
from data_to_paper.research_types.scientific_research.scientific_products import ScientificProducts
from data_to_paper.servers.crossref import CrossrefCitation


@dataclass
class ProduceScientificPaperPDFWithAppendix(BaseLatexToPDF):
    products: ScientificProducts = None

    def _get_title(self) -> str:
        return self.products.get_title()

    def _get_abstract(self) -> str:
        return self.products.get_abstract()

    def _get_sections(self) -> Dict[str, str]:
        return {section_name: self.products.tabled_paper_sections[section_name]
                for section_name in self.paper_section_names}

    def _get_references(self) -> List[CrossrefCitation]:
        return self.products.citations

    def _get_appendix(self):
        s = ''
        s += self.products.data_file_descriptions.to_latex()
        for code_and_output in self.products.codes_and_outputs.values():
            s += '\n\n' + code_and_output.to_latex()
        return s
