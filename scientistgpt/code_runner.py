import re
import os
from typing import Optional

from scientistgpt.exceptions import FailedExtractingCode, FailedLoadingOutput, FailedRunningCode

CODE_REGEXP = "```python\n(.*?)\n```"


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
        matches = re.findall(CODE_REGEXP, self.response, re.DOTALL)
        if len(matches) != 1:
            raise FailedExtractingCode(len(matches))
        return matches[0].strip()

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
        try:
            exec(code)
        except Exception as e:
            raise FailedRunningCode(e)
        return self.read_output_file()
