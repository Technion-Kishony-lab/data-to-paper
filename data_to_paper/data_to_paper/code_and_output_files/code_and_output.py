from __future__ import annotations

from dataclasses import dataclass, field

from typing import Optional, Any, TYPE_CHECKING, Dict

from data_to_paper.base_products import DataFileDescriptions
from data_to_paper.code_and_output_files.file_view_params import ContentView, ContentViewPurpose
from data_to_paper.code_and_output_files.ref_numeric_values import HypertargetFormat, HypertargetPosition
from data_to_paper.latex.clean_latex import wrap_as_latex_code_output, replace_special_latex_chars
from data_to_paper.run_gpt_code.base_run_contexts import RunContext

from data_to_paper.code_and_output_files.output_file_requirements import OutputFileRequirementsWithContent

if TYPE_CHECKING:
    from data_to_paper.run_gpt_code.overrides.dataframes.dataframe_operations import DataframeOperations


@dataclass
class CodeAndOutput:
    name: str = None
    code: str = None
    result: Any = None
    created_files: \
        OutputFileRequirementsWithContent = field(default_factory=OutputFileRequirementsWithContent)
    code_name: str = None
    code_explanation: Optional[str] = None
    provided_code: Optional[str] = None
    contexts: Optional[Dict[str, RunContext]] = None
    dataframe_operations: Optional[DataframeOperations] = None
    description_of_created_files: DataFileDescriptions = None

    def to_latex(self, content_view: ContentView) -> str:
        s = f"\\section{{{self.name}}}\n"
        if self.code:
            s += "\\subsection{{Code}}\n"
            s += f"The {self.name} was carried out using the following custom code:\n"
            s += '\n\\begin{python}\n' + self.code + '\n\\end{python}\n\n'
        if self.provided_code:
            s += f"\\subsection{{Provided Code}}\n"
            s += f"The code above is using the following provided functions:\n"
            s += '\n\\begin{python}\n' + self.provided_code + '\n\\end{python}\n\n'
        if self.code_explanation:
            s += "\\subsection{Code Description}\n"
            s += '\n' + self.code_explanation

        outputs = self.created_files.get_created_content_files_to_referencable_text(content_view=content_view)
        if outputs:
            s += '\n\n' + "\\subsection{Code Output}"
            for filename, output in outputs.items():
                content, references = output.get_hypertarget_text_and_header_references(content_view)
                s += '\n'.join(reference.to_str(HypertargetFormat(HypertargetPosition.HEADER))
                               for reference in references)
                s += f'\n\n\\subsubsection*{{{replace_special_latex_chars(filename)}}}'
                s += '\n\n' + wrap_as_latex_code_output(content)
        return s

    def to_text(self):
        s = f"{self.name} Code and Output\n"
        if self.code:
            s += "Code:\n"
            s += self.code + '\n\n'
        if self.provided_code:
            s += "Provided Code:\n"
            s += self.provided_code + '\n\n'
        if self.code_explanation:
            s += "Code Description:\n"
            s += self.code_explanation + '\n\n'
        outputs = self.created_files.get_created_content_files_to_pretty_contents(
            content_view=ContentViewPurpose.FINAL_APPENDIX)

        if outputs:
            s += "Code Output:\n"
            for filename, output in outputs.items():
                s += f'\n\n{filename}\n'
                s += '\n' + output
        return s
