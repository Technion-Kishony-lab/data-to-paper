import re
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from scientistgpt.run_gpt_code.dynamic_code import run_code_using_module_reload

from .types import CodeAndOutput
from .exceptions import FailedExtractingCode, FailedLoadingOutput

# different code formats that we have observed in chatgpt responses:
POSSIBLE_CODE_HEADERS = ["```python\n", "``` python\n", "```\n", "``` \n"]
CORRECT_CODE_HEADER = "```python\n"
CODE_REGEXP = f'{CORRECT_CODE_HEADER}(.*?)\n```'


LINES_ADDED_BY_MODIFYING_CODE = 0


def add_python_to_first_triple_quotes_if_missing(content: str):
    """
    Add "python" to triple quotes if missing.
    We assume the first triple quotes are the code block.
    """
    first_triple_quotes = content.find('```')

    if first_triple_quotes == -1:
        return content

    first_triple_quotes_end = content.find('\n', first_triple_quotes)
    if first_triple_quotes_end == -1:
        return content
    first_triple_quotes_line = content[first_triple_quotes:first_triple_quotes_end + 1]
    if first_triple_quotes_line in POSSIBLE_CODE_HEADERS:
        return content.replace(first_triple_quotes_line, CORRECT_CODE_HEADER, 1)
    return content


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
    output_file: Optional[str] = None
    script_file: Optional[str] = None
    data_folder: Optional[Path] = None

    @property
    def output_file_path(self) -> Optional[Path]:
        if self.data_folder is None:
            return self.output_file
        return self.data_folder / self.output_file

    def extract_code(self) -> str:
        num_block_edges = self.response.count('```')
        if num_block_edges == 2:
            corrected_content = add_python_to_first_triple_quotes_if_missing(self.response)
            matches = re.findall(CODE_REGEXP, corrected_content, re.DOTALL)
            if len(matches) == 1:
                return matches[0].strip()
        raise FailedExtractingCode(num_block_edges)

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
        run_code_using_module_reload(code,
                                     save_as=None,  # change to self.script_file in order to keep records of the code
                                     run_in_folder=self.data_folder,
                                     allowed_read_files=self.allowed_read_files,
                                     allowed_write_files=None if self.output_file is None else [self.output_file])
        return CodeAndOutput(code=code, output=self.read_output_file(), output_file=self.output_file)
