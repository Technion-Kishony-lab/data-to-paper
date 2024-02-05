from dataclasses import dataclass
from typing import Dict, List, Tuple

from data_to_paper.base_steps import BaseLatexToPDF
from data_to_paper.latex.latex_to_pdf import evaluate_latex_num_command
from data_to_paper.research_types.scientific_research.scientific_products import ScientificProducts
from data_to_paper.servers.crossref import CrossrefCitation


@dataclass
class ProduceScientificPaperPDFWithAppendix(BaseLatexToPDF):
    products: ScientificProducts = None

    def _get_formatted_section_and_notes(self, section_name: str) -> Tuple[str, Dict[str, str]]:
        section = self.products.tabled_paper_sections[section_name]
        return evaluate_latex_num_command(section, ref_prefix=section_name.replace(' ', '_'))

    def _get_sections(self) -> Dict[str, str]:
        return {section_name: self._get_formatted_section_and_notes(section_name)[0]
                for section_name in self.paper_section_names}

    def _get_references(self) -> List[CrossrefCitation]:
        return self.products.citations

    def _get_all_notes(self):
        notes = {}
        for section_name in self.paper_section_names:
            _, section_notes = self._get_formatted_section_and_notes(section_name)
            notes.update(section_notes)
        return notes

    def _get_notes_appendix(self):
        notes = self._get_all_notes()
        if not notes:
            return ''
        return f"\\section{{Notes}}\n\n\\noindent" + \
            '\n\n'.join([f'\\hypertarget{{{note}}}{{{text}}}' for note, text in notes.items()])

    def _get_appendix(self):
        s = ''
        s += self.products.data_file_descriptions.to_latex(should_hypertarget=True)
        for code_name, code_and_output in self.products.codes_and_outputs.items():
            s += '\n\n' + code_and_output.to_latex(should_hypertarget=code_name == 'data_analysis')
        notes_appendix = self._get_notes_appendix()
        if notes_appendix:
            s += '\n\n' + notes_appendix
        return s
