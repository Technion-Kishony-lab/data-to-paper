from dataclasses import dataclass
from typing import Optional

from scientistgpt.cast import Agent
from scientistgpt.conversation.message_designation import RangeMessageDesignation
from scientistgpt.env import SUPPORTED_PACKAGES
from scientistgpt.gpt_interactors.debugger_gpt import DebuggerGPT
from scientistgpt.gpt_interactors.step_by_step.base_scientific_conversers import BaseScientificGPT
from scientistgpt.run_gpt_code.code_runner import CodeAndOutput
from scientistgpt.utils import dedent_triple_quote_str, is_code_in_response


BASE_GPT_SCRIPT_FILE_NAME = 'gpt_code'
MAX_CODE_REVISIONS = 3
MAX_CODE_WRITING_ATTEMPTS = 3
MAX_DEBUG_ITERATIONS_PER_ATTEMPT = 12
MAX_REGENERATING_MULTI_CHOICE_RESPONSE = 3


@dataclass
class BaseCodeScientificGPT(BaseScientificGPT):
    output_filename: str = 'results.txt'
    "The name of the file that gpt code is instructed to save the results to."

    gpt_script_filename: str = BASE_GPT_SCRIPT_FILE_NAME
    "The base name of the python file in which the code written by gpt is saved."


@dataclass
class CodeFeedbackGPT(BaseCodeScientificGPT):
    background_product_fields = ['data_file_descriptions', 'research_goal', 'analysis_plan']
    conversation_name: str = 'code_debugging'
    assistant_agent: Agent = Agent.Debugger
    user_agent: Agent = Agent.Student
    revision_round: int = 0

    def get_output_filename(self):
        if self.revision_round == 0:
            return self.output_filename
        else:
            return self.output_filename.replace('.', f'_revision_{self.revision_round}.')

    @property
    def _request_code_tag(self):
        return f'code_revision_{self.revision_round}'

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
            user_prompt = dedent_triple_quote_str("""
                Write a complete short Python code to perform the data analysis plan.
                If needed, you can use the following packages in your code: {}.
                The output of your code should be a text file named "{}".
                All results we may need for a scientific paper should be saved to that file, including \
                analysis findings, summary statistics, etc. 
                Do not write to any other files and do not plot anything to screen.
            """).format(SUPPORTED_PACKAGES, self.get_output_filename())
        else:
            user_prompt = dedent_triple_quote_str("""
                Revise the code, or just change any key parameters (like thresholds, etc) within the code as needed.
                The output of your new code should be a text file named "{}".
                Send me back the complete revised code.
                Do not just point to what needs to be changed, send the full complete code.
                """).format(self.get_output_filename())
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
                conversation_name=self.conversation_name,
                user_agent=self.user_agent,
                assistant_agent=self.assistant_agent,
                output_filename=self.get_output_filename(),
                data_files=self.products.data_filenames,
                max_debug_iterations=MAX_DEBUG_ITERATIONS_PER_ATTEMPT,
                gpt_script_filename=f"{self.gpt_script_filename}_attempt{attempt}",
                previous_code=previous_code,
            ).run_debugging()
            if code_and_output is None:
                # debugging failed
                self.comment(f'Debugging failed, {revision_and_attempt}.')
                continue

            # debugging succeeded. we now forge the conversation as if chatgpt immediately sent the correct code:
            self.conversation_manager.delete_messages(
                message_designation=RangeMessageDesignation.from_(start=start_tag, end=-1),
                comment='Deleting all debugging correspondence.')
            assert self.conversation[-1].tag == self._request_code_tag

            self.apply_append_surrogate_message(
                content=dedent_triple_quote_str("""
                Here is the code to perform the analysis. It saves results to the file "{}".
                ```python
                {}
                ```
                """).format(self.get_output_filename(), code_and_output.code),
                comment='Adding the debugged code as if it was the original response.',
                is_code=True,
            )
            return code_and_output
        return None

    def _ask_for_code_explanation(self) -> str:
        self.apply_append_user_message(
            content=dedent_triple_quote_str("""
            Please explain what your code does. Do not provide a line-by-line explanation, rather provide a \
            high-level explanation of the code in a language suitable for a Methods section of a research \
            paper. Also explain what does the code writes into the {} file.
            """).format(self.output_filename),
        )
        return self.apply_get_and_append_assistant_message()

    def _ask_chatgpt_whether_further_code_revisions_are_needed(self, code_and_output: CodeAndOutput) -> Optional[int]:
        user_prompt = dedent_triple_quote_str("""
            I ran your code. Here is the content of the output file ({}):
            ```
            {}
            ```

            Please choose one of the following options:

            a. The results seem reasonable. Let's proceed.

            b. Something is wrong. I need to go back and change the code.

            Answer with just the letter designating the option you choose \
            (only type a single character: "a", or "b").
            """).format(
            self.get_output_filename(),
            code_and_output.output,
        )
        self.apply_append_user_message(content=user_prompt, tag='output_file_content')

        response = self.apply_get_and_append_assistant_message()
        for num_tries in range(MAX_REGENERATING_MULTI_CHOICE_RESPONSE):
            if 'a' in response and 'b' not in response and len(response) < 5:
                self.comment('ScientistGPT declared it is satisfied with the analysis.')
                return 1
            elif 'b' in response and 'a' not in response and len(response) < 5:
                self.comment(f'ScientistGPT declared it needs to revise the code. Starting a new revision.'
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
                        comment='ScientistGPT did not choose a valid option. Regenerating response.')
        return None
