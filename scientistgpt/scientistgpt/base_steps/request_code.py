from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from scientistgpt.conversation.message_designation import RangeMessageDesignation
from scientistgpt.env import SUPPORTED_PACKAGES
from scientistgpt.run_gpt_code.types import CodeAndOutput
from scientistgpt.utils import dedent_triple_quote_str, is_code_in_response
from scientistgpt.utils.replacer import with_attribute_replacement
from scientistgpt.utils.text_utils import NiceList

from .debugger_gpt import DebuggerGPT
from .base_products_conversers import BaseProductsGPT

BASE_GPT_SCRIPT_FILE_NAME = 'gpt_code'
MAX_CODE_REVISIONS = 3
MAX_CODE_WRITING_ATTEMPTS = 3
MAX_DEBUG_ITERATIONS_PER_ATTEMPT = 12
MAX_REGENERATING_MULTI_CHOICE_RESPONSE = 3


@dataclass
class BaseCodeProductsGPT(BaseProductsGPT):
    revision_round: int = 0

    fake_performer_request_for_help: str = "Hi, could you please help me write code for my project?"
    fake_reviewer_agree_to_help: str = "Well, I think this is something you can do yourself, but I am certainly " \
                                       "happy to provide guidance and feedback.\n" \
                                       "Please just provide some background and context first.\n"

    output_filename: str = 'results.txt'
    "The name of the file that gpt code is instructed to save the results to."

    gpt_script_filename: str = BASE_GPT_SCRIPT_FILE_NAME
    "The base name of the python file in which the code written by gpt is saved."

    code_requesting_prompt: str = dedent_triple_quote_str("""
        Write a complete short Python code to perform the data analysis plan.
        Don't state what the code should do in comments, write the code itself.
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
        I ran your code. Here is the content of the output file ({{}}):
        ```
        {{}}
        ```

        Please choose one of the following options:

        a. The results seem reasonable. Let's proceed.

        b. Something is wrong. I need to go back and change the code.

        Answer with just the letter designating the option you choose \
        (only type a single character: "a", or "b").
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
        while self.revision_round < MAX_CODE_REVISIONS:
            self._ask_for_code()
            code_and_output = self._run_debugger(code_and_output.code)
            if code_and_output is None:
                return None
            gpt_choice = self._ask_chatgpt_whether_further_code_revisions_are_needed(code_and_output)
            if gpt_choice == 1:
                code_and_output.explanation = self._ask_for_code_explanation()
                return code_and_output
            self.revision_round += 1
        return None

    def _ask_for_code(self):
        if self.revision_round == 0:
            user_prompt = self.code_requesting_prompt.format(SUPPORTED_PACKAGES, self._get_output_filename())
        else:
            user_prompt = self.code_revision_requesting_prompt.format(self._get_output_filename())
        self.apply_append_user_message(user_prompt, tag=self._request_code_tag)

    def _run_debugger(self, previous_code: Optional[str] = None) -> Optional[CodeAndOutput]:
        start_tag = self._request_code_tag + '_debugging'
        for attempt in range(MAX_CODE_WRITING_ATTEMPTS):
            # in each attempt, we are resetting the conversation back to this tag:
            revision_and_attempt = f"Revision {self.revision_round + 1}/{MAX_CODE_REVISIONS} " \
                                   f"(attempt {attempt + 1}/{MAX_CODE_WRITING_ATTEMPTS})"
            self.comment(f'Transfer to DebuggerGPT {revision_and_attempt}.', tag=start_tag)

            # we now call the debugger that will try to run and provide feedback in multiple iterations:
            code_and_output = DebuggerGPT(
                actions_and_conversations=self.actions_and_conversations,
                conversation_name=self.conversation_name,
                user_agent=self.user_agent,
                assistant_agent=self.assistant_agent,
                output_filename=self._get_output_filename(),
                data_files=self.data_filenames,
                data_folder=self.data_folder,
                max_debug_iterations=MAX_DEBUG_ITERATIONS_PER_ATTEMPT,
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
                    show_on_web=False,
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

    def _ask_chatgpt_whether_further_code_revisions_are_needed(self, code_and_output: CodeAndOutput) -> Optional[int]:
        if self.offer_revision_prompt is None:
            return 1

        user_prompt = self.offer_revision_prompt.format(
            self._get_output_filename(),
            code_and_output.output,
        )
        self.apply_append_user_message(content=user_prompt, tag='output_file_content')

        response = self.apply_get_and_append_assistant_message(max_tokens=1)
        for num_tries in range(MAX_REGENERATING_MULTI_CHOICE_RESPONSE):
            if 'a' in response and 'b' not in response and len(response) < 5:
                self.comment('ChatGPT declared it is satisfied with the analysis.')
                return 1
            elif 'b' in response and 'a' not in response and len(response) < 5:
                self.comment(f'ChatGPT declared it needs to revise the code. Starting a new revision.'
                             f'({self.revision_round + 1}/{MAX_CODE_REVISIONS}).')
                return 2
            elif is_code_in_response(response):
                # the scientist sent code, so we assume it wants to change the code (choosing "2")
                response = self.conversation_manager.replace_last_response(
                    content='b',
                    comment='ChatGPT sent code instead of "a"/"b". We assume it wants to change the code ("b").')
            else:
                if num_tries < MAX_REGENERATING_MULTI_CHOICE_RESPONSE - 1:
                    response = self.conversation_manager.regenerate_previous_response(
                        comment='ChatGPT did not choose a valid option. Regenerating response.')
        return None
