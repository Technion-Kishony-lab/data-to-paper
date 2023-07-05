from dataclasses import dataclass
from typing import Optional, List

from data_to_paper.base_products import DataFileDescriptions
from data_to_paper.latex.clean_latex import process_non_math_parts, wrap_with_lstlisting
from data_to_paper.run_gpt_code.overrides.dataframes import DataframeOperations


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

    def to_latex(self):
        s = f"\\section{{{self.name}}} \\subsection{{Code}}" \
            f"The {self.name} was carried out using the following custom code:"
        s += '\n\n'
        s += '\\begin{minted}[linenos, breaklines]{python}\n' + self.code + '\n\\end{minted}\n\n'
        if self.code_explanation:
            s += "\\subsection{Code Description}"
            s += '\n\n' + process_non_math_parts(self.code_explanation)
        if self.output:
            s += '\n\n' + "\\subsection{Code Output}"
            s += '\n\n' + wrap_with_lstlisting(self.output)
        return s
