from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Any, TYPE_CHECKING, Dict

from data_to_paper.base_products.file_descriptions import DataFileDescriptions
from data_to_paper.code_and_output_files.file_view_params import ViewPurpose
from data_to_paper.code_and_output_files.output_file_requirements import OutputFileRequirementsToFileToContent
from data_to_paper.code_and_output_files.ref_numeric_values import HypertargetFormat, HypertargetPosition, \
    ReferencedValue
from data_to_paper.code_and_output_files.referencable_text import convert_str_to_latex_label
from data_to_paper.latex.clean_latex import wrap_as_latex_code_output, replace_special_latex_chars, \
    replace_non_utf8_chars
from data_to_paper.run_gpt_code.base_run_contexts import RunContext
from data_to_paper.text import wrap_as_block
from data_to_paper.text.highlighted_text import format_text_with_code_blocks

if TYPE_CHECKING:
    from data_to_paper.run_gpt_code.overrides.dataframes.dataframe_operations import DataframeOperations


@dataclass
class CodeAndOutput:
    name: str = None
    code: str = None
    result: Any = None
    created_files: \
        OutputFileRequirementsToFileToContent = field(default_factory=OutputFileRequirementsToFileToContent)
    code_name: str = None
    code_explanation: Optional[str] = None
    provided_code: Optional[str] = None
    contexts: Optional[Dict[str, RunContext]] = None
    dataframe_operations: Optional[DataframeOperations] = None
    description_of_created_files: DataFileDescriptions = None

    def _get_file_requirement_and_content(self, filename: str):
        return self.created_files.get_created_files_to_requirements_and_contents()[filename]

    def _get_file_requirement(self, filename: str):
        return self._get_file_requirement_and_content(filename)[0]

    def get_code_line_str_for_file(self, filename: str) -> Optional[str]:
        """
        Return a string which can be found in the line where we should go to when we want to see the code
        that created the file.
        """
        requirement, content = self._get_file_requirement_and_content(filename)
        return requirement.get_code_line_str_for_file(filename, content)

    def get_lineno_for_file(self, code: str, filename: str) -> Optional[int]:
        header = self.get_code_line_str_for_file(filename)
        if header is None:
            return None
        lines = code.split('\n')
        for i, line in enumerate(lines):
            if header in line:
                return i + 1
        return None

    @staticmethod
    def _add_hypertarget_to_code(code: str, label: str, lineno: int) -> str:
        """
        Add hypertarget to the code at the beginning of the line with the lineno
        """
        lines = code.split('\n')
        hypertarget_format = HypertargetFormat(position=HypertargetPosition.WRAP, raised=True, escaped=True)
        lines[lineno - 1] = ReferencedValue('', label).to_str(hypertarget_format) + lines[lineno - 1]
        return '\n'.join(lines)

    def _get_code_line_label_for_file(self, filename: str) -> str:
        requirement, content = self._get_file_requirement_and_content(filename)
        return requirement.get_code_line_label_for_file(filename, content)

    def _get_hypertarget_for_appendix_file_header(self, filename: str) -> str:
        return ReferencedValue(
            value='',
            label=convert_str_to_latex_label(filename, 'file'),
            is_target=True).to_str(HypertargetFormat(position=HypertargetPosition.WRAP))

    def _get_hyperlinked_header_for_appendix_file(self, filename: str) -> str:
        return ReferencedValue(
            value=replace_special_latex_chars(filename),
            label=self._get_hyperlink_label_for_file_header(filename),
            is_target=False).to_str(HypertargetFormat(position=HypertargetPosition.WRAP))

    def _get_hyperlink_label_for_file_header(self, filename: str) -> str:
        requirement, content = self._get_file_requirement_and_content(filename)
        return requirement.get_hyperlink_label_for_file_header(filename, content)

    def _get_code_with_hypertargets(self) -> str:
        code = self.code
        for filename in self.created_files.get_created_content_files():
            lineno = self.get_lineno_for_file(code, filename)
            if lineno is not None:
                code = self._add_hypertarget_to_code(
                    code, self._get_code_line_label_for_file(filename), lineno)
        return code

    def as_latex_for_appendix(self) -> str:
        s = f"\\section{{{self.name}}}\n"
        if self.code:
            s += "\\subsection{{Code}}\n"
            s += f"The {self.name} was carried out using the following custom code:\n"
            s += '\n\\begin{python}\n' + self._get_code_with_hypertargets() + '\n\\end{python}\n\n'
        if self.provided_code:
            s += f"\\subsection{{Provided Code}}\n"
            s += f"The code above is using the following provided functions:\n"
            s += '\n\\begin{python}\n' + self.provided_code + '\n\\end{python}\n\n'
        if self.code_explanation:
            s += "\\subsection{Code Description}\n"
            s += '\n' + self.code_explanation

        outputs = self.created_files.get_created_content_files_to_pretty_contents(
            view_purpose=ViewPurpose.FINAL_APPENDIX, header_level=None)
        if outputs:
            s += '\n\n' + "\\subsection{Code Output}"
            for filename, content in outputs.items():
                hypertarget = self._get_hypertarget_for_appendix_file_header(filename)
                hyperlinked_header = self._get_hyperlinked_header_for_appendix_file(filename)
                s += f'\n{hypertarget}\n\n\\subsubsection*{{{hyperlinked_header}}}'
                s += '\n\n' + wrap_as_latex_code_output(content)
        s = replace_non_utf8_chars(s)
        return s

    def to_text(self, with_header: bool = True):
        s = ''
        if with_header:
            if self.name is None:
                s = f"# Code and Output\n"
            else:
                s = f"# {self.name} Code and Output\n"
        if self.code:
            s += "## Code:\n"
            s += wrap_as_block(self.code, 'python') + '\n'
        if self.provided_code:
            s += "## Provided Code:\n"
            s += wrap_as_block(self.provided_code, 'python') + '\n'
        if self.code_explanation:
            s += "## Code Description:\n"
            s += wrap_as_block(self.code_explanation, 'latex') + '\n'
        if self.created_files:
            outputs = self.created_files.get_created_content_files_to_pretty_contents(
                view_purpose=ViewPurpose.APP_HTML, header_level=3)
        else:
            outputs = None

        if outputs:
            s += "## Code Output:\n"
            for filename, output in outputs.items():
                s += f"### {wrap_as_block(output, 'html')}\n"
        return s

    def as_html(self):
        return format_text_with_code_blocks(self.to_text(), from_md=True, is_html=True)
