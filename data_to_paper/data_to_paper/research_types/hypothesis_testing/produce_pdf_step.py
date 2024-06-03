from dataclasses import dataclass
from typing import Dict, List, Tuple

from data_to_paper.base_steps import BaseLatexToPDF
from data_to_paper.code_and_output_files.file_view_params import ViewPurpose
from data_to_paper.latex.latex_to_pdf import evaluate_latex_num_command
from data_to_paper.research_types.hypothesis_testing.scientific_products import ScientificProducts
from data_to_paper.code_and_output_files.ref_numeric_values import ReferencedValue
from data_to_paper.code_and_output_files.referencable_text import ListReferenceableText
from data_to_paper.servers.custom_types import Citation


@dataclass
class ProduceScientificPaperPDFWithAppendix(BaseLatexToPDF):
    products: ScientificProducts = None

    def _get_formatted_section_and_notes(self, section_name: str) -> Tuple[str, Dict[str, str]]:
        section = self.products.get_tabled_paper_sections(ViewPurpose.FINAL_INLINE)[section_name]
        return evaluate_latex_num_command(section, ref_prefix=section_name.replace(' ', '_'))

    def _get_sections(self) -> Dict[str, str]:
        return {section_name: self._get_formatted_section_and_notes(section_name)[0]
                for section_name in self.paper_section_names}

    def _get_references(self) -> List[Citation]:
        return self.products.get_all_cited_citations()

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
        text = ListReferenceableText(text='\n'.join([r'\item{@}'] * len(notes)),
                                     hypertarget_prefix='',
                                     pattern='@',
                                     reference_list=[ReferencedValue(label=key, value=value, is_target=True)
                                                     for key, value in notes.items()]
                                     )

        # no_indent = "\\setlength{\\itemindent}{0em}\n\\setlength{\\leftmargini}{0em}\n"
        no_indent = ""
        return f"\\section{{Calculation Notes}}\n{no_indent}\\begin{{itemize}}\n" \
            + text.get_hypertarget_text_with_header(content_view=ViewPurpose.FINAL_INLINE) \
            + "\n\\end{itemize}"

    def _get_appendix(self):
        s = ''
        s += self.products.data_file_descriptions.to_latex(view_purpose=ViewPurpose.FINAL_APPENDIX)
        for code_name, code_and_output in self.products.codes_and_outputs.items():
            s += '\n\n' + code_and_output.as_latex_for_appendix(view_purpose=ViewPurpose.FINAL_APPENDIX)
        notes_appendix = self._get_notes_appendix()
        if notes_appendix:
            s += '\n\n' + notes_appendix
        return s
