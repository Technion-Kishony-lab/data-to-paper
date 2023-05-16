from dataclasses import dataclass
from typing import Optional


@dataclass
class CodeAndOutput:
    name: str = None
    code: str = None
    output: str = None
    output_file: Optional[str] = None
    code_name: str = None
    explanation: Optional[str] = None
