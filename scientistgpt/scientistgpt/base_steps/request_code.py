from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from scientistgpt.conversation.message_designation import RangeMessageDesignation
from scientistgpt.env import SUPPORTED_PACKAGES
from scientistgpt.run_gpt_code.types import CodeAndOutput
from scientistgpt.utils import dedent_triple_quote_str
from scientistgpt.utils.replacer import with_attribute_replacement
from scientistgpt.utils.text_utils import NiceList

from .debugger_gpt import DebuggerGPT
from .base_products_conversers import BaseProductsGPT
from .exceptions import FailedCreatingProductException
from .request_multi_choice import BaseMultiChoiceProductsGPT

BASE_GPT_SCRIPT_FILE_NAME = 'gpt_code'
MAX_REGENERATING_MULTI_CHOICE_RESPONSE = 3


@dataclass
class BaseCodeProductsGPT(BaseProductsGPT):
    max_code_revisions: int = 3
    max_code_writing_attempts: int = 2
    max_debug_iterations_per_attempt: int = 12

    revision_round: int = 0

    system_prompt: str = dedent_triple_quote_str("""
        You are a brilliant data scientist. You are writing a Python code to analyze data.
        """)

    fake_performer_request_for_help: str = "Hi {user_skin_name}, could you please help me write code for my project?"
    fake_reviewer_agree_to_help: str = "Hey {assistant_skin_name} - I think this is something you can do yourself, " \
                                       "but I am certainly happy to provide guidance and feedback.\n" \
                                       "I suggest that you start with providing some background and context first.\n"

    output_filename: str = 'results.txt'
    "The name of the file that gpt code is instructed to save the results to."

    gpt_script_filename: str = BASE_GPT_SCRIPT_FILE_NAME
    "The base name of the python file in which the code written by gpt is saved."

    code_requesting_prompt: str = dedent_triple_quote_str("""
        Write a complete short Python code to perform the data analysis plan.
        Don't provide a sketch or pseudocode; write a complete runnable code.
        If needed, you can use the following packages in your code: {{}}.
        The output of your code should be a text file named "{{}}".
        """)

    code_revision_requesting_prompt: str = dedent_triple_quote_str("""
        Revise the code, or just change any key parameters within the code as needed.
        The output of your new code should be a text file named "{{}}".
        Send me back the complete revised code.
        Do not just point to what needs to be changed, send the full complete code.
        """)

    present_code_as_fresh: str = dedent_triple_quote_str("""
        Here is the code to perform the analysis. It saves results to the file "{{}}".
        ```python
        {{}}
        ```
        """)  # set to None to not present code

    requesting_code_explanation_prompt: str = dedent_triple_quote_str("""
        Please explain what your code does. 
        Also explain what does the code writes into the {{}} file.
        """)  # set to None to skip asking for explanation

    offer_revision_prompt: str = dedent_triple_quote_str("""
        I ran your code. Here is the content of the output file that it created ("{{}}"):
        ```
        {{}}
        ```

        Please choose one of the following options:

        1. The results seem reasonable. Let's proceed.

        2. Something is wrong. I need to go back and change the code.
        """)  # set to None to skip option for revision

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

    def _get_output_filename(self):
        if self.revision_round == 0:
            return self.output_filename
        else:
            return self.output_filename.replace('.', f'_revision_{self.revision_round}.')

    @property
    def _request_code_tag(self):
        return f'code_revision_{self.revision_round}'

    @with_attribute_replacement
    def get_analysis_code(self) -> Optional[CodeAndOutput]:
        self.initialize_conversation_if_needed()
        self._pre_populate_background()
        code_and_output = CodeAndOutput()
        while self.revision_round < self.max_code_revisions:
            self._ask_for_code()
            code_and_output = self._run_debugger(code_and_output.code)
            if code_and_output is None:
                raise FailedCreatingProductException(product_field='code_and_output')
            gpt_choice = self._ask_chatgpt_whether_further_code_revisions_are_needed(code_and_output)
            if gpt_choice == '1':
                code_and_output.explanation = self._ask_for_code_explanation()
                return code_and_output
            self.revision_round += 1
        raise FailedCreatingProductException(product_field='code_and_output')

    def _ask_for_code(self):
        if self.revision_round == 0:
            user_prompt = self.code_requesting_prompt.format(SUPPORTED_PACKAGES, self._get_output_filename())
        else:
            user_prompt = self.code_revision_requesting_prompt.format(self._get_output_filename())
        self.apply_append_user_message(user_prompt, tag=self._request_code_tag)

    def _run_debugger(self, previous_code: Optional[str] = None) -> Optional[CodeAndOutput]:
        start_tag = self._request_code_tag + '_debugging'
        for attempt in range(self.max_code_writing_attempts):
            # in each attempt, we are resetting the conversation back to this tag:
            revision_and_attempt = f"Revision {self.revision_round + 1}/{self.max_code_revisions} " \
                                   f"(attempt {attempt + 1}/{self.max_code_writing_attempts})"
            self.comment(f'Starting to write and debug code. {revision_and_attempt}.', tag=start_tag)

            # we now call the debugger that will try to run and provide feedback in multiple iterations:
            code_and_output = DebuggerGPT.from_(
                self,
                output_filename=self._get_output_filename(),
                data_files=self.data_filenames,
                data_folder=self.data_folder,
                max_debug_iterations=self.max_debug_iterations_per_attempt,
                gpt_script_filename=f"{self.gpt_script_filename}_attempt{attempt}",
                previous_code=previous_code,
            ).run_debugging()
            if code_and_output is None:
                # debugging failed
                self.comment(f'Debugging failed, {revision_and_attempt}.')
                continue

            if self.present_code_as_fresh:
                # debugging succeeded. we now forge the conversation as if chatgpt immediately sent the correct code:
                self.conversation_manager.delete_messages(
                    message_designation=RangeMessageDesignation.from_(start=start_tag, end=-1),
                    comment='Deleting all debugging correspondence.')
                assert self.conversation[-1].tag == self._request_code_tag

                self.apply_append_surrogate_message(
                    content=self.present_code_as_fresh.format(self._get_output_filename(), code_and_output.code),
                    comment='Adding the debugged code as if it was the original response.',
                    web_conversation_name=None,
                )
            return code_and_output
        return None

    def _ask_for_code_explanation(self) -> Optional[str]:
        if self.requesting_code_explanation_prompt is None:
            return None
        self.apply_append_user_message(
            content=self.requesting_code_explanation_prompt.format(self.output_filename),
        )
        return self.apply_get_and_append_assistant_message()

    def _ask_chatgpt_whether_further_code_revisions_are_needed(self, code_and_output: CodeAndOutput) -> Optional[str]:
        if self.offer_revision_prompt is None:
            return '1'

        return BaseMultiChoiceProductsGPT(
            conversation_name=self.conversation_name,
            web_conversation_name=self.web_conversation_name,
            user_agent=self.user_agent,
            assistant_agent=self.assistant_agent,
            actions_and_conversations=self.actions_and_conversations,
            multi_choice_question=self.offer_revision_prompt.format(self._get_output_filename(),
                                                                    code_and_output.output),
            possible_choices=('1', '2'),
        ).get_chosen_option()
