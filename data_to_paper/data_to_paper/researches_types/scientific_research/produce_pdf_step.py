from dataclasses import dataclass
from typing import Dict, List

from data_to_paper.base_steps import BaseLatexToPDFWithAppendix
from data_to_paper.researches_types.scientific_research.scientific_products import ScientificProducts
from data_to_paper.servers.crossref import CrossrefCitation


@dataclass
class ProduceScientificPaperPDFWithAppendix(BaseLatexToPDFWithAppendix):
    products: ScientificProducts = None

    def _choose_sections_to_add_to_paper_and_collect_references(self) -> (Dict[str, str], List[CrossrefCitation]):
        sections, references = super()._choose_sections_to_add_to_paper_and_collect_references()
        added_sections = {section_name: self.products.tabled_paper_sections[section_name]
                          for section_name in self.get_paper_section_names()}
        added_references = self.products.citations
        return {**sections, **added_sections}, references + added_references

    def _create_appendix(self):
        s = self.products.data_file_descriptions.to_latex()
        for code_step in self.products.codes_and_outputs:
            s += '\n\n' + self.products.codes_and_outputs[code_step].to_latex()
        return s
