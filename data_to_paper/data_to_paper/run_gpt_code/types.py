from dataclasses import dataclass
from typing import Optional, List

from pygments import highlight
from pygments.formatters.latex import LatexFormatter
from pygments.lexers import PythonLexer

from data_to_paper.base_products import DataFileDescriptions
from data_to_paper.latex.latex_to_pdf import replace_special_chars, wrap_with_lstlisting
from data_to_paper.run_gpt_code.overrides.dataframes import DataframeOperations
from data_to_paper.utils.text_formatting import wrap_python_code


@dataclass
class CodeAndOutput:
    name: str = None
    code: str = None
    output: str = None
    output_file: Optional[str] = None
    created_files: List[str] = None
    code_name: str = None
    code_explanation: Optional[str] = None
    dataframe_operations: Optional[DataframeOperations] = None
    description_of_created_files: DataFileDescriptions = None

    def get_created_files_beside_output_file(self) -> List[str]:
        """
        Return the names of the files created by the run, except the output file.
        """
        if self.created_files is None:
            return []
        return [file for file in self.created_files if file != self.output_file]

    def to_latex(self, width: int = 80, latex_formatter=None):
        s = f"\\section{{{self.name}}} \\subsection{{Code}}" \
            f"The {self.name} was carried out using the following custom code:"
        s += '\n\n'
        s += '\\begin{minted}[linenos, breaklines]{python}\n' + self.code + '\n\\end{minted}\n\n'
        if self.code_explanation:
            s += "\\subsection{Code Description}"
            s += '\n\n' + replace_special_chars(self.code_explanation)
        if self.output:
            s += '\n\n' + "\\subsection{Code Output}"
            s += '\n\n' + wrap_with_lstlisting(self.output)
        return s
