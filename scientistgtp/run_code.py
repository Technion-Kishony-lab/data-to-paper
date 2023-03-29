import re
import os
from dataclasses import dataclass
from typing import Optional

CODE_REGEXP = r"```python(.*?)```"


class RunCoodeException(Exception):
    pass


@dataclass
class FailedExtractingCode(RunCoodeException):
    number_of_codes: int

    def __str__(self):
        if self.number_of_codes == 0:
            return "No code was found."
        return "More than one code snippet was found."


@dataclass
class FailedRunningCode(RunCoodeException):
    exception: Exception

    def __str__(self):
        return f"Running the code resulted in the following exception:\n{self.exception}\n"


class FailedLoadingOutput(RunCoodeException, FileNotFoundError):
    def __str__(self):
        return "Output file not found."


class RunCode:
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
