import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Iterable, Tuple

from data_to_paper.run_gpt_code.dynamic_code import run_code_using_module_reload
from data_to_paper.run_gpt_code.code_utils import extract_code_from_text
from data_to_paper.utils import line_count

from .types import CodeAndOutput, OutputFileRequirement
from .runtime_issues_collector import RuntimeIssueCollector


@dataclass
class CodeRunner:
    """
    CodeRunner facilitates extracting and running Python code from chatGPT response::
    1. Extract code from GPT response.
    2. Run code, raise a relevant exception with text to send to chatGPT.
    3. Read the output file created by the run if successful.
    """

    response: str
    add_in_front_of_code: str = ''
    allowed_read_files: Iterable[str] = ()
    output_file_requirements: Tuple[OutputFileRequirement, ...] = ()
    allow_dataframes_to_change_existing_series: bool = True
    script_file_path: Optional[Path] = None
    data_folder: Optional[Path] = None

    @property
    def lines_added_in_front_of_code(self) -> int:
        return line_count(self.add_in_front_of_code)

    @property
    def keep_content_allowed_created_filenames(self) -> Tuple[str, ...]:
        return tuple(requirement.filename for requirement in self.output_file_requirements
                     if requirement.should_keep_content)

    @property
    def all_allowed_created_filenames(self) -> Tuple[str, ...]:
        return tuple(requirement.filename for requirement in self.output_file_requirements)

    def extract_code(self) -> str:
        return extract_code_from_text(self.response)

    def modify_extracted_code(self, code: str) -> str:
        """
        Modify the extracted code before running it.
        """
        code = code.replace('from my_utils', 'from data_to_paper.run_gpt_code.run_utils')
        return self.add_in_front_of_code + code

    def extract_and_modify_code(self) -> str:
        """
        Extract code from GPT response, and modify it before running it.
        """
        code = self.extract_code()
        modified_code = self.modify_extracted_code(code)
        assert len(code.splitlines()) == len(modified_code.splitlines()) - self.lines_added_in_front_of_code
        return modified_code

    def read_output_file(self, output_file: str, delete_file: bool = False) -> str:
        """
        Return the content of the output file created by the run if successful.
        """
        filepath = self.data_folder / output_file if self.data_folder else output_file
        with open(filepath, 'r') as file:
            content = file.read()
        if delete_file:
            os.remove(filepath)
        return content

    def run_code(self) -> Tuple[CodeAndOutput, RuntimeIssueCollector]:
        """
        Run code from GPT response, and return the output and the code.
        """
        code = self.extract_and_modify_code()
        created_files, dataframe_operations, issue_collector = run_code_using_module_reload(
            code=code,
            save_as=self.script_file_path,
            allowed_read_files=self.allowed_read_files,
            allowed_write_files=self.all_allowed_created_filenames,
            allow_dataframes_to_change_existing_series=self.allow_dataframes_to_change_existing_series,
            run_in_folder=self.data_folder)
        return CodeAndOutput(
            code=code,
            requirements_to_output_files_to_contents={requirement: {
                output_file: (self.read_output_file(output_file, delete_file=True)
                              if requirement.should_keep_content else None)
                for output_file in created_files
                if requirement.matches(output_file)
            } for requirement in self.output_file_requirements},
            dataframe_operations=dataframe_operations), issue_collector
