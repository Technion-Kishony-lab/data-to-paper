from dataclasses import dataclass
from typing import Optional, Set


@dataclass
class CodeAndOutput:
    name: str = None
    code: str = None
    output: str = None
    output_file: Optional[str] = None
    created_files: Set[str] = None
    code_name: str = None
    explanation: Optional[str] = None

    def get_created_files_beside_output_file(self) -> Set[str]:
        return self.created_files - {self.output_file}
