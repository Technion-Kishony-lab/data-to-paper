import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Iterable, Tuple

from data_to_paper.run_gpt_code.dynamic_code import RunCode
from data_to_paper.run_gpt_code.code_utils import extract_code_from_text
from data_to_paper.utils import line_count
from .overrides.dataframes import TrackDataFrames
from .run_context import IssueCollector

from .types import CodeAndOutput, OutputFileRequirement


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

    runtime_available_objects: dict = field(default_factory=dict)

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
        modified_code = code.replace('from my_utils',
                                     'from data_to_paper.utils_for_gpt_code.utils_modified_for_gpt_use')
        modified_code = self.add_in_front_of_code + modified_code
        assert line_count(code) == line_count(modified_code) - self.lines_added_in_front_of_code
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

    def run_code(self) -> Tuple[CodeAndOutput, IssueCollector]:
        """
        Run code from GPT response, and return the output and the code.
        """
        code = self.extract_code()
        modified_code = self.modify_extracted_code(code)

        contexts = RunCode(
            allowed_open_read_files=self.allowed_read_files,
            allowed_open_write_files=self.all_allowed_created_filenames,
            allowed_create_files=self.all_allowed_created_filenames,
            allow_dataframes_to_change_existing_series=self.allow_dataframes_to_change_existing_series,
            run_in_folder=self.data_folder,
            runtime_available_objects=self.runtime_available_objects,
        ).run(code=modified_code, save_as=self.script_file_path)

        issue_collector: IssueCollector = contexts['IssueCollector']
        track_df: TrackDataFrames = contexts['TrackDataFrames']
        dataframe_operations = track_df.dataframe_operations
        track_created_files = contexts['TrackCreatedFiles']
        return CodeAndOutput(
            code=code,
            requirements_to_output_files_to_contents={requirement: {
                output_file: (self.read_output_file(output_file, delete_file=True)
                              if requirement.should_keep_content else None)
                for output_file in track_created_files.created_files
                if requirement.matches(output_file)
            } for requirement in self.output_file_requirements},
            dataframe_operations=dataframe_operations), issue_collector
