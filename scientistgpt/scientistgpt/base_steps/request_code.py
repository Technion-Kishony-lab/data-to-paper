from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from scientistgpt.conversation.message_designation import RangeMessageDesignation
from scientistgpt.env import SUPPORTED_PACKAGES
from scientistgpt.run_gpt_code.types import CodeAndOutput
from scientistgpt.utils import dedent_triple_quote_str
from scientistgpt.utils.nice_list import NiceList
from scientistgpt.utils.replacer import Replacer

from .debugger import DebuggerConverser
from .base_products_conversers import BackgroundProductsConverser
from .exceptions import FailedCreatingProductException
from .request_multi_choice import MultiChoiceBackgroundProductsConverser


@dataclass
class BaseCodeProductsGPT(BackgroundProductsConverser):
    max_code_revisions: int = 3
    max_code_writing_attempts: int = 2
    max_debug_iterations_per_attempt: int = 12

    supported_packages: Tuple[str, ...] = SUPPORTED_PACKAGES

    allowed_created_files: Tuple[str, ...] = None
    # e.g. ('*.csv', '*.txt'), or `None` for any file.  No need to include the output file, it is added automatically.

    allow_dataframes_to_change_existing_series: bool = True
    enforce_saving_altered_dataframes: bool = False

    revision_round: int = 0

    system_prompt: str = dedent_triple_quote_str("""
        You are a brilliant data scientist. You are writing a Python code to analyze data.
        """)

    goal_noun: str = '{code_name} code'
    goal_verb: str = 'write'
    user_initiation_prompt: str = 'Please write a code to analyze the data.'

    output_filename: str = 'results.txt'
    # The name of the file that gpt code is instructed to save the results to.

    code_name: str = ''  # e.g. "data analysis"

    gpt_script_filename: str = 'gpt_code'
    # The base name of the python file in which the code written by gpt is saved.

    code_revision_requesting_prompt: str = dedent_triple_quote_str("""
        Revise the code as needed to correct the above issues.
        The output of your new code should be a text file named "{actual_output_filename}".
        Do not just point to what needs to be changed; send the full complete revised code.
        """)

    present_code_as_fresh: str = dedent_triple_quote_str("""
        Here is the code to perform the analysis.
        {code_save_result_to_file_explanation}
        ```python
        {}
        ```
        """)  # set to None to not present code

    offer_revision_prompt: str = dedent_triple_quote_str("""
        I ran your code. Here is the content of the output file that it created ("{actual_output_filename}"):
        ```
        {}
        ```

        Please check if there is anything wrong in these results (like unexpected NaN values, or anything else \
        that may indicate that code improvements are needed), then choose one of the following options:

        1. The results seem reasonable. Let's proceed.

        2. Something is wrong. I need to go back and change/improve the code.

        {choice_instructions}
        """)  # set to None to skip option for revision

    @property
    def code_save_result_to_file_explanation(self) -> str:
        if self.output_filename is None:
            return ''
        return 'It saves results to the file "{actual_output_filename}".'

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
    def actual_output_filename(self):
        if self.revision_round == 0:
            return self.output_filename
        else:
            return self.output_filename.replace('.', f'_revision_{self.revision_round}.')

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
        start_tag = self._request_code_tag + '_debugging'
        for attempt in range(self.max_code_writing_attempts):
            # in each attempt, we are resetting the conversation back to this tag:
            revision_and_attempt = f"Revision {self.revision_round + 1}/{self.max_code_revisions} " \
                                   f"(attempt {attempt + 1}/{self.max_code_writing_attempts})"
            self.comment(f'Starting to write and debug code. {revision_and_attempt}.', tag=start_tag)

            # we now call the debugger that will try to run and provide feedback in multiple iterations:
            code_and_output = DebuggerConverser.from_(
                self,
                is_new_conversation=False,
                output_filename=self.actual_output_filename,
                data_files=self.data_filenames,
                data_folder=self.data_folder,
                max_debug_iterations=self.max_debug_iterations_per_attempt,
                gpt_script_filename=f"{self.gpt_script_filename}_attempt{attempt}",
                previous_code=previous_code,
                allowed_created_files=self.allowed_created_files,
                allow_dataframes_to_change_existing_series=self.allow_dataframes_to_change_existing_series,
                enforce_saving_altered_dataframes=self.enforce_saving_altered_dataframes,
            ).run_debugging()
            if code_and_output is None:
                # debugging failed
                self.comment(f'Debugging failed, {revision_and_attempt}.')
                continue

            if self.present_code_as_fresh:
                # debugging succeeded. we now forge the conversation as if chatgpt immediately sent the correct code:
                self.apply_delete_messages(
                    message_designation=RangeMessageDesignation.from_(start=start_tag, end=-1),
                    comment='Deleting all debugging correspondence.')

                self.apply_append_surrogate_message(
                    content=Replacer(self, self.present_code_as_fresh, args=(code_and_output.code,)),
                    comment='Adding the debugged code as if it was the original response.',
                    web_conversation_name=None,
                )
            return code_and_output
        return None

    def _are_further_code_revisions_needed(self, code_and_output: CodeAndOutput) -> bool:
        if self.offer_revision_prompt is None or self.output_filename is None:
            return False

        return MultiChoiceBackgroundProductsConverser.from_(
            self,
            is_new_conversation=False,
            user_initiation_prompt=Replacer(self, self.offer_revision_prompt, args=(code_and_output.output,)),
            possible_choices=('1', '2'),
        ).run_and_get_valid_result() == '2'
