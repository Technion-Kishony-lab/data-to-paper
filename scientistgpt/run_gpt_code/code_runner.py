import re
import os
from typing import Optional

from scientistgpt.run_gpt_code.dynamic_code import run_code_from_file

from .exceptions import FailedExtractingCode, FailedLoadingOutput

# different code formats that we have observed in chatgpt responses:
CODE_REGEXPS = ["```python\n(.*?)\n```", "``` python\n(.*?)\n```", "```\n(.*?)\n```"]


class CodeRunner:
    """
    CodeRunner facilitates extracting and running Python code from chatGPT response::
    1. Extract code from GPT response.
    2. Run code, raise a relevant exception with text to send to chatGPT.
    3. Read the output file created by the run if successful.
    """

    def __init__(self,
                 response: str,
                 output_file: Optional[str],
                 script_file: Optional[str] = None):
        self.response = response
        self.output_file = output_file
        self.script_file = script_file

    def extract_code(self):
        num_block_edges = self.response.count('```')
        if num_block_edges == 2:
            for regexp in CODE_REGEXPS:
                matches = re.findall(regexp, self.response, re.DOTALL)
                if len(matches) == 1:
                    return matches[0].strip()
        raise FailedExtractingCode(num_block_edges // 2)

    def read_output_file(self):
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

    def run_code(self):
        code = self.extract_code()
        self.delete_output_file()
        run_code_from_file(code, self.script_file)
        return self.read_output_file()
