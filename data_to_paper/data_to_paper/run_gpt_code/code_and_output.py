from __future__ import annotations

from dataclasses import dataclass, field

from typing import Optional, Any, TYPE_CHECKING

from data_to_paper.base_products import DataFileDescriptions
from data_to_paper.latex.clean_latex import wrap_with_lstlisting, replace_special_latex_chars

from .output_file_requirements import OutputFileRequirementsWithContent

if TYPE_CHECKING:
    from .overrides.dataframes.dataframe_operations import DataframeOperations


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
    dataframe_operations: Optional[DataframeOperations] = None
    description_of_created_files: DataFileDescriptions = None

    def to_latex(self):
        s = f"\\section{{{self.name}}}\n"
        if self.code:
            s += "\\subsection{{Code}}\n"
            s += f"The {self.name} was carried out using the following custom code:\n"
            s += '\n\\begin{minted}[linenos, breaklines]{python}\n' + self.code + '\n\\end{minted}\n\n'
        if self.provided_code:
            s += f"\\subsection{{Provided Code}}\n"
            s += f"The code above is using the following provided functions:\n"
            s += '\n\\begin{minted}[linenos, breaklines]{python}\n' + self.provided_code + '\n\\end{minted}\n\n'
        if self.code_explanation:
            s += "\\subsection{Code Description}\n"
            s += '\n' + self.code_explanation
        outputs = self.created_files.get_created_content_files_to_contents()
        if outputs:
            s += '\n\n' + "\\subsection{Code Output}"
            for filename, output in outputs.items():
                s += f'\n\n\\subsubsection*{{{replace_special_latex_chars(filename)}}}'
                s += '\n\n' + wrap_with_lstlisting(output)
        return s
