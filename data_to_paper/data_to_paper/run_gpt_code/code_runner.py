import os
from abc import abstractmethod, ABC
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Iterable, Tuple, List, Dict, Any, Type

from data_to_paper.run_gpt_code.dynamic_code import RunCode
from data_to_paper.run_gpt_code.code_utils import extract_code_from_text
from data_to_paper.utils import line_count

from .types import CodeAndOutput, OutputFileRequirement, RunIssue


@dataclass
class BaseCodeRunner(ABC):
    response: str = None  # response from ChatGPT (with code)
    script_file_path: Optional[Path] = None  # where to save the script after running. If None, don't save.
    run_folder: Optional[Path] = None
    output_file_requirements: Tuple[OutputFileRequirement, ...] = ()
    allowed_read_files: Iterable[str] = ()
    additional_contexts: Dict[str, Any] = field(default_factory=dict)  # additional contexts to use when running code
    runtime_available_objects: dict = field(default_factory=dict)
    run_code_cls: Type[RunCode] = RunCode
    _lines_added_in_front_of_code: int = None

    @property
    def lines_added_in_front_of_code(self) -> int:
        return self._lines_added_in_front_of_code

    @abstractmethod
    def get_raw_code(self) -> str:
        """
        Extract the raw code from the response.
        """
        return NotImplementedError

    @property
    def keep_content_allowed_created_filenames(self) -> Tuple[str, ...]:
        return tuple(requirement.filename for requirement in self.output_file_requirements
                     if requirement.should_keep_content)

    @property
    def all_allowed_created_filenames(self) -> Tuple[str, ...]:
        return tuple(requirement.filename for requirement in self.output_file_requirements)

    def _modify_code(self, code: str) -> Tuple[str, int]:
        """
        Modify the raw code before running it.
        For example, add imports, change imports, etc.
        Return the modified code and the number of lines added in front of the code.
        """
        return code, 0

    def get_modified_code_for_run(self, code: str) -> str:
        """
        Get the actual code for running.
        """
        modified_code, self._lines_added_in_front_of_code = self._modify_code(code)
        return modified_code

    def get_run_code(self) -> RunCode:
        """
        Get the code for running.
        """
        return self.run_code_cls(
            allowed_open_read_files=self.allowed_read_files,
            allowed_open_write_files=self.all_allowed_created_filenames,
            allowed_create_files=self.all_allowed_created_filenames,
            run_folder=self.run_folder,
            runtime_available_objects=self.runtime_available_objects,
            additional_contexts=self.additional_contexts,
        )

    def read_output_file(self, output_file: str, delete_file: bool = False) -> str:
        """
        Return the content of the output file created by the run if successful.
        """
        filepath = self.run_folder / output_file if self.run_folder else output_file
        with open(filepath, 'r') as file:
            content = file.read()
        if delete_file:
            os.remove(filepath)
        return content

    def _get_requirements_to_output_files_to_contents(self, created_files: Iterable[str]) -> dict:
        """
        Return a dictionary mapping each requirement to a dictionary mapping each output file to its content.
        """
        return {requirement: {
            output_file: (self.read_output_file(output_file, delete_file=True)
                          if requirement.should_keep_content else None)
            for output_file in created_files
            if requirement.matches(output_file)
        } for requirement in self.output_file_requirements}

    def _get_code_and_output(self, code: str, result: str, created_files: Iterable[str],
                             contexts: Dict[str, Any] = None) -> CodeAndOutput:
        """
        Return the CodeAndOutput object for the given result and created files.
        """
        return CodeAndOutput(
            code=code,
            result=result,
            requirements_to_output_files_to_contents=self._get_requirements_to_output_files_to_contents(created_files),
        )

    def run_code(self) -> Tuple[CodeAndOutput, List[RunIssue], Dict[str, Any]]:
        """
        Run code from GPT response, and return the output and the code.
        """
        code = self.get_raw_code()
        modified_code = self.get_modified_code_for_run(code)

        result, created_files, issues, contexts = \
            self.get_run_code().run(code=modified_code, save_as=self.script_file_path)

        return self._get_code_and_output(code, result, created_files, contexts), issues, contexts


@dataclass
class CodeRunner(BaseCodeRunner):
    """
    CodeRunner facilitates extracting and running Python code from chatGPT response::
    1. Extract code from GPT response.
    2. Run code, raise a relevant exception with text to send to chatGPT.
    3. Read the output file created by the run if successful.
    """

    add_in_front_of_code: str = ''

    def get_raw_code(self) -> str:
        return extract_code_from_text(self.response)

    def _modify_code(self, code: str) -> Tuple[str, int]:
        """
        Modify the extracted code before running it.
        """
        modified_code = code.replace('from my_utils',
                                     'from data_to_paper.utils_for_gpt_code.utils_modified_for_gpt_use')
        modified_code = self.add_in_front_of_code + modified_code
        return modified_code, line_count(self.add_in_front_of_code)
