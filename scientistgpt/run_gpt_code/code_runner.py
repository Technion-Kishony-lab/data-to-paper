import re
import os
from dataclasses import dataclass
from typing import Optional, NamedTuple

from scientistgpt.run_gpt_code.dynamic_code import run_code_from_file

from .exceptions import FailedExtractingCode, FailedLoadingOutput

# different code formats that we have observed in chatgpt responses:
CODE_REGEXPS = ["```python\n(.*?)\n```", "``` python\n(.*?)\n```", "```\n(.*?)\n```"]


CodeAndOutput = NamedTuple('CodeAndOutput', [('code', str), ('output', str)])


LINES_ADDED_BY_MODIFYING_CODE = 1


@dataclass
class CodeRunner:
    """
    CodeRunner facilitates extracting and running Python code from chatGPT response::
    1. Extract code from GPT response.
    2. Run code, raise a relevant exception with text to send to chatGPT.
    3. Read the output file created by the run if successful.
    """

    response: str
    output_file: Optional[str]
    script_file: Optional[str] = None

    def extract_code(self) -> str:
        num_block_edges = self.response.count('```')
        if num_block_edges == 2:
            for regexp in CODE_REGEXPS:
                matches = re.findall(regexp, self.response, re.DOTALL)
                if len(matches) == 1:
                    return matches[0].strip()
        raise FailedExtractingCode(num_block_edges)

    def modify_extracted_code(self, code: str) -> str:
        """
        Modify the extracted code before running it.
        """
        # add imports of fake forbidden functions:
        code = 'from scientistgpt.run_gpt_code.fake_functions import *\n' + code
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
            with open(self.output_file, 'r') as file:
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
        run_code_from_file(code, self.script_file)
        return CodeAndOutput(code, self.read_output_file())
