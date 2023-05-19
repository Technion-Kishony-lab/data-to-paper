import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from scientistgpt.run_gpt_code.dynamic_code import run_code_using_module_reload
from scientistgpt.utils.code_utils import extract_code_from_text

from .types import CodeAndOutput
from .exceptions import FailedExtractingCode, FailedLoadingOutput


LINES_ADDED_BY_MODIFYING_CODE = 0


@dataclass
class CodeRunner:
    """
    CodeRunner facilitates extracting and running Python code from chatGPT response::
    1. Extract code from GPT response.
    2. Run code, raise a relevant exception with text to send to chatGPT.
    3. Read the output file created by the run if successful.
    """

    response: str
    allowed_read_files: Optional[list] = None
    allow_creating_files: bool = False
    output_file: Optional[str] = None
    script_file_path: Optional[Path] = None
    data_folder: Optional[Path] = None

    @property
    def output_file_path(self) -> Optional[Path]:
        if self.data_folder is None:
            return self.output_file
        return self.data_folder / self.output_file

    def extract_code(self) -> str:
        num_block_edges = self.response.count('```')
        if num_block_edges != 2:
            raise FailedExtractingCode(num_block_edges)
        return extract_code_from_text(self.response)

    def modify_extracted_code(self, code: str) -> str:
        """
        Modify the extracted code before running it.
        """
        return code

    def extract_and_modify_code(self) -> str:
        """
        Extract code from GPT response, and modify it before running it.
        """
        code = self.extract_code()
        modified_code = self.modify_extracted_code(code)
        assert len(code.splitlines()) == len(modified_code.splitlines()) - LINES_ADDED_BY_MODIFYING_CODE
        return modified_code

    def read_output_file(self) -> Optional[str]:
        """
        Return the content of the output file created by the run if successful.
        """
        if self.output_file is None:
            return None
        try:
            with open(self.output_file_path, 'r') as file:
                return file.read()
        except FileNotFoundError:
            raise FailedLoadingOutput()

    def delete_output_file(self):
        try:
            os.remove(self.output_file)
        except FileNotFoundError:
            pass

    def run_code(self) -> CodeAndOutput:
        """
        Run code from GPT response, and return the output and the code.
        """
        code = self.extract_and_modify_code()
        self.delete_output_file()
        created_files = run_code_using_module_reload(
            code=code,
            save_as=self.script_file_path,  # None to delete
            run_in_folder=self.data_folder,
            allowed_read_files=self.allowed_read_files,
            allowed_write_files=None if self.allow_creating_files else
            ([] if self.output_file is None else [self.output_file]),
        )
        return CodeAndOutput(
            code=code,
            output=self.read_output_file(),
            output_file=self.output_file,
            created_files=created_files,
        )
