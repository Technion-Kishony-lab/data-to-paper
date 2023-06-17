from dataclasses import dataclass
from typing import Optional, List

from data_to_paper.base_products import DataFileDescriptions
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
