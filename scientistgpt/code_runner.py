import re
import os
from typing import Optional

from scientistgpt.dynamic_code import run_code_from_file
from scientistgpt.exceptions import FailedExtractingCode, FailedLoadingOutput

# different code formats that we have been observed in chatgpt responses:
CODE_REGEXPS = ["```python\n(.*?)\n```", "``` python\n(.*?)\n```", "```\n(.*?)\n```"]


class CodeRunner:
    """
    CodeRunner facilitates running code from chatGPT response:
    1. Extract code from GPT response.
    2. Run code
    3. Read file created by the run.
    """
    
    def __init__(self, response: str, output_file: Optional[str]):
        self.response = response
        self.output_file = output_file
        self.code = None

    def extract_code(self):
        for regexp in CODE_REGEXPS:
            matches = re.findall(regexp, self.response, re.DOTALL)
            if len(matches) == 1:
                return matches[0].strip()
        raise FailedExtractingCode(len(matches))

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
        run_code_from_file(code)
        return self.read_output_file()
