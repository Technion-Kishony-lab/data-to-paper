from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple, Dict

from data_to_paper.env import SUPPORTED_PACKAGES
from data_to_paper.run_gpt_code.types import CodeAndOutput, OutputFileRequirement, ContentOutputFileRequirement, \
    get_single_content_file_from_requirements
from data_to_paper.utils import dedent_triple_quote_str
from data_to_paper.utils.nice_list import NiceList
from data_to_paper.utils.replacer import Replacer

from .debugger import DebuggerConverser
from .base_products_conversers import BackgroundProductsConverser
from .exceptions import FailedCreatingProductException
from .request_python_value import PythonDictWithDefinedKeysAndValuesReviewBackgroundProductsConverser


@dataclass
class BaseCodeProductsGPT(BackgroundProductsConverser):
    max_code_revisions: int = 5
    max_code_writing_attempts: int = 2
    max_debug_iterations_per_attempt: int = 12
    background_product_fields_to_hide_during_code_revision: Tuple[str, ...] = ()
    supported_packages: Tuple[str, ...] = SUPPORTED_PACKAGES

    allow_dataframes_to_change_existing_series: bool = True
    enforce_saving_altered_dataframes: bool = False

    revision_round: int = 0

    system_prompt: str = dedent_triple_quote_str("""
        You are a brilliant data scientist. You are writing a Python code to analyze data.
        """)

    goal_noun: str = '{code_name} code'
    goal_verb: str = 'write'
    user_initiation_prompt: str = 'Please write a code to analyze the data.'

    output_file_requirements: Tuple[OutputFileRequirement, ...] = (ContentOutputFileRequirement('results.txt'), )
    # The name of the file that gpt code is instructed to save the results to.

    code_name: str = ''  # e.g. "data analysis"

    gpt_script_filename: str = 'gpt_code'
    # The base name of the python file in which the code written by gpt is saved.

    code_revision_requesting_prompt: str = dedent_triple_quote_str("""
        Revise the code as needed to correct the above issues.
        Do not just point to what needs to be changed; send the full complete revised code.
        """)

    present_code_as_fresh: str = dedent_triple_quote_str("""
        Here is the code to perform the analysis.
        {created_file_names_explanation}
        ```python
        {code}
        ```
        """)  # set to None to not present code

    offer_revision_prompt: str = dedent_triple_quote_str("""
        I ran your code. 
        
        {created_file_contents_explanation}

        Please check if there is anything wrong in these results (like unexpected NaN values, or anything else \
        that may indicate that code improvements are needed), then choose one of the following options:

        1. The results seem reasonable, I am happy with the code and the results, {'choice': 'ok'}.  

        2. Something is wrong. I need to go back and change/improve the code, {'choice': 'revise'}.

        Return your choice as a Python Dict[str, str], with either: {'choice': 'ok'} or {'choice': 'revise'}.
        """)  # set to None to skip option for revision

    @property
    def output_filename(self) -> str:
        return get_single_content_file_from_requirements(self.output_file_requirements)

    def get_created_file_names_explanation(self, code_and_output: CodeAndOutput) -> str:
        created_files = code_and_output.get_created_content_files_to_contents()
        if len(created_files) == 0:
            return ''
        elif len(created_files) == 1:
            created_file = next(iter(created_files))
            return f'It saves the results to the file "{created_file}".'
        else:
            return f'It saves the results to the files {list(created_files)}.'

    def get_created_file_contents_explanation(self, code_and_output: CodeAndOutput) -> Optional[str]:
        files_to_contents = code_and_output.get_created_content_files_to_contents(is_clean=True)
        if len(files_to_contents) == 0:
            return None
        s = 'Here is the content of the output file(s) that the code created:\n'
        for filename, content in files_to_contents.items():
            s += f'"{filename}":\n```output\n{content}\n```'
        return s

    @property
    def data_filenames(self) -> NiceList[str]:
        """
        The names of the files that gpt code can access.
        Need to be overridden by subclasses, to include the names of the data files from Products
        """
        return NiceList([],
                        wrap_with='"',
                        prefix='{} data file[s]: ')

    @property
    def data_folder(self) -> Optional[Path]:
        """
        The folder in which the data files are located.
        Need to be overridden by subclasses, to include the folder of the data files from Products
        """
        return None

    @property
    def _request_code_tag(self):
        return f'code_revision_{self.revision_round}'

    def get_code_and_output(self) -> Optional[CodeAndOutput]:
        self.initialize_conversation_if_needed()
        code_and_output = CodeAndOutput()
        while self.revision_round < self.max_code_revisions:
            if self.revision_round > 0:
                self.apply_append_user_message(self.code_revision_requesting_prompt)
            code_and_output = self._run_debugger(code_and_output.code)
            if code_and_output is None:
                raise FailedCreatingProductException()
            if not self._are_further_code_revisions_needed(code_and_output):
                break
            self.revision_round += 1
        else:
            raise FailedCreatingProductException()
        code_and_output.name = self.code_name
        return code_and_output

    def _run_debugger(self, previous_code: Optional[str] = None) -> Optional[CodeAndOutput]:
        for attempt in range(self.max_code_writing_attempts):
            # in each attempt, we are resetting the conversation back to this tag:
            revision_and_attempt = f"Revision {self.revision_round + 1}/{self.max_code_revisions} " \
                                   f"(attempt {attempt + 1}/{self.max_code_writing_attempts})"
            self.comment(f'Starting to write and debug code. {revision_and_attempt}.')

            # we now call the debugger that will try to run and provide feedback in multiple iterations:
            code_and_output = DebuggerConverser.from_(
                self,
                is_new_conversation=False,
                output_file_requirements=self.output_file_requirements,
                data_filenames=self.data_filenames,
                data_folder=self.data_folder,
                max_debug_iterations=self.max_debug_iterations_per_attempt,
                gpt_script_filename=f"{self.gpt_script_filename}_revision{self.revision_round}_attempt{attempt}",
                background_product_fields_to_hide=
                () if self.revision_round == 0 else self.background_product_fields_to_hide_during_code_revision,
                previous_code=previous_code,
                allow_dataframes_to_change_existing_series=self.allow_dataframes_to_change_existing_series,
                enforce_saving_altered_dataframes=self.enforce_saving_altered_dataframes,
                supported_packages=self.supported_packages,
                model_engine=self.model_engine,
            ).run_debugging()
            if code_and_output is None:
                # debugging failed
                self.comment(f'Debugging failed, {revision_and_attempt}.')
                continue

            if self.present_code_as_fresh:
                # debugging succeeded. we now forge the conversation as if ChatGPT immediately sent the correct code:
                self._rewind_conversation_to_first_response()
                self.apply_append_surrogate_message(
                    content=Replacer(
                        self, self.present_code_as_fresh,
                        kwargs=dict(
                            code=code_and_output.code,
                            created_file_names_explanation=self.get_created_file_names_explanation(code_and_output),
                        )),
                    comment='Adding the debugged code as if it was the original response.',
                    web_conversation_name=None,
                )
            return code_and_output
        return None

    def _are_further_code_revisions_needed(self, code_and_output: CodeAndOutput) -> bool:
        created_file_contents_explanation = self.get_created_file_contents_explanation(code_and_output)
        if self.offer_revision_prompt is None or created_file_contents_explanation is None:
            return False

        return PythonDictWithDefinedKeysAndValuesReviewBackgroundProductsConverser.from_(
            self,
            value_type=Dict[str, str],
            allowed_values_for_keys={'choice': ['ok', 'revise']},
            is_new_conversation=False,
            user_initiation_prompt=Replacer(
                self, self.offer_revision_prompt,
                kwargs=dict(
                    created_file_contents_explanation=created_file_contents_explanation,
                )),
        ).run_and_get_valid_result()['choice'] == 'revise'
