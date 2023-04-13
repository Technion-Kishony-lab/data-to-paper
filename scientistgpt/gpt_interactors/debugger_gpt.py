import os
from dataclasses import dataclass
from typing import Optional

from scientistgpt.conversation.message_designation import RangeMessageDesignation, SingleMessageDesignation
from scientistgpt.run_gpt_code.code_runner import CodeRunner, CodeAndOutput
from scientistgpt.env import SUPPORTED_PACKAGES
from scientistgpt.utils import dedent_triple_quote_str
from scientistgpt.run_gpt_code.exceptions import FailedExtractingCode, FailedRunningCode, FailedLoadingOutput, \
    CodeUsesForbiddenFunctions

from scientistgpt.gpt_interactors.converser_gpt import CodeWritingGPT


@dataclass
class DebuggerGPT(CodeWritingGPT):
    """
    Interact with chatgpt to debug a code that needs to create an output file.

    Starting with a conversation which ends with a code-request from the user, DebuggerGPT interacts with chatgpt to
    enhance the code until it runs properly and creates a desired output file.

    Interactions with chatgpt include adequate reporting of:
    * missing packages
    * trying to load wrong files
    * syntax errors
    * runtime exceptions
    * too long runs (timeout)
    * output file not created
    """

    agent: str = 'DEBUGGER'
    max_debug_iterations: int = 5

    debug_iteration = 0
    initiation_tag: Optional[str] = None

    @property
    def iteration_str(self):
        return f'Debug iteration {self.debug_iteration}/{self.max_debug_iterations}'

    def _run_code_from_response(self, response: str) -> CodeAndOutput:
        script_file = f'{self.gpt_script_filename}_{self.debug_iteration}'
        result = CodeRunner(response=response,
                            output_file=self.output_filename,
                            script_file=script_file,
                            ).run_code()
        os.rename(self.output_filename, script_file + '.txt')
        return result

    def _specify_allowed_packages(self, error_message: str):
        self.conversation_manager.append_user_message(
            content=dedent_triple_quote_str("""
            I ran the code and got the following error message:
            ```
            {}
            ```
            Please rewrite the code using only these packages: {}. 
            """).format(error_message, ', '.join(SUPPORTED_PACKAGES)),
            comment=f'{self.iteration_str}: ImportError detected in gpt code.')

    def _specify_file_not_found(self, error_message: str):
        self.conversation_manager.append_user_message(
            content=dedent_triple_quote_str("""
            I ran the code and got the following error message:
            ```
            {}
            ```
            Please note that we only have the files that I noted in the data description above. 
            All of these files are in the same directory as the code. 
            """).format(error_message),
            comment=f'{self.iteration_str}: FileNotFound detected in gpt code.')

    def _specify_error_message(self, error_message: str):
        self.conversation_manager.append_user_message(
            content=dedent_triple_quote_str("""
            I ran the code and got the following error message:
            ```
            {}
            ```
            Please rewrite the complete code again with this error corrected. 
            """).format(error_message),
            comment=f'{self.iteration_str}: Runtime exception in GPT code.')

    def _specify_missing_output(self):
        self.conversation_manager.append_user_message(
            content=dedent_triple_quote_str("""
            I ran the code, but it didn't generate the desired output file ({}).
            Please rewrite the complete code again with this error corrected. 
            """).format(self.output_filename),
            comment=f'{self.iteration_str}: Code completed, but no output file created.')

    def _specify_timeout(self):
        self.conversation_manager.append_user_message(
            content=dedent_triple_quote_str("""
            I ran the code, but it just ran forever...
            Please fix and rewrite the complete code again so that it doesn't get stuck. 
            """),
            comment=f'{self.iteration_str}: GPT code has timed out.')

    def _respond_to_missing_or_incomplete_code(self, number_of_code_edges: int):
        """
        We notify missing or incomplete code to chatgpt.
        If the conversation already has this notification, we regenerate gpt response instead.
        """
        if number_of_code_edges == 0:
            response = dedent_triple_quote_str("""
            You did not send any code. 
            Please try again, make sure your code is inside a triple-quoted code block (```).
            """)
            tag = 'no_code'
        elif number_of_code_edges % 2 == 1:
            response = dedent_triple_quote_str("""
            Your code is incomplete. Please try again with a shorter code.
            """)
            tag = 'incomplete_code'
        else:
            response = dedent_triple_quote_str("""
            Please send your code in a single code block.
            """)
            tag = 'multiple_code_blocks'

        # We use a tagged message to rewind back in case the same problem repeats
        self.conversation_manager.append_user_message(
            content=response,
            tag=tag,
            comment=f'{self.iteration_str}: Failed extracting code from gpt response. Notifying.'
        )

    def _notify_forbidden_functions(self, func: str):
        if func == 'print':
            self.conversation_manager.append_user_message(
                content=dedent_triple_quote_str("""
                Please do not use the `print` function. 
                Anything you want to print, must be written to the output file. 
                """),
                comment=f'{self.iteration_str}: Code uses `print`.')
            return
        self.conversation_manager.append_user_message(
            content=dedent_triple_quote_str("""
            I ran the code, but it used the function `{}` which is not allowed.
            Please rewrite the complete code again without using this function. 
            """).format(func),
            comment=f'{self.iteration_str}: Code uses forbidden function {func}.')

    def _get_and_run_code(self) -> Optional[CodeAndOutput]:
        """
        Get a code from chatgpt, run it and return code and result.
        If the code fails, notify chatgpt and return None.
        """
        response = self.conversation_manager.get_and_append_assistant_message()
        failed_extracting_code = False
        try:
            code_and_output = self._run_code_from_response(response)
        except FailedExtractingCode as e:
            failed_extracting_code = True
            self._respond_to_missing_or_incomplete_code(e.number_of_code_edges)
        except FailedRunningCode as e:
            try:
                raise e.exception
            except ImportError:
                # chatgpt tried using a package we do not support
                self._specify_allowed_packages(str(e.exception))
            except TimeoutError:
                # code took too long to run
                self._specify_timeout()
            except FileNotFoundError:
                # the code tried to load file that we do not have
                self._specify_file_not_found(str(e.exception))
            except CodeUsesForbiddenFunctions as f:
                self._notify_forbidden_functions(f.func)
            except Exception:
                # the code failed on other errors
                # we will indicate to chatgpt the error message that we got
                self._specify_error_message(e.get_traceback_message())
        except FailedLoadingOutput:
            # Code ran, but the output file was not created.
            self._specify_missing_output()
        except Exception:
            raise
        else:
            # The code ran successfully
            self.conversation_manager.append_commenter_message(
                "GPT code completed successfully. Returning results to MentorGPT.")
            return code_and_output
        # if code was extracted ok, we clean up a bit, deleting the previous debug iterations
        if not failed_extracting_code:
            self.conversation_manager.delete_messages(
                message_designation=RangeMessageDesignation.from_(
                    SingleMessageDesignation(tag=self.initiation_tag, off_set=1), -3),  # keeps the last 2 messages
                comment="Deleting previous debug iterations.")
        return None  # code failed

    def _get_or_create_tag(self):
        """
        If the last message has a tag, use it as the initiation tag.
        Otherwise, create a new tag tagged comment and use it as the initiation tag.
        """
        if self.initiation_tag is None:
            if self.conversation[-1].tag:
                self.initiation_tag = self.conversation[-1].tag
            else:
                raise ValueError("The last message must have a tag.")

    def run_debugging(self) -> Optional[CodeAndOutput]:
        """
        Run the debugging process.
        If debugging did not converge to a running code within the max_debug_iterations, return None.
        Otherwise, return the code and output.
        """
        self._get_or_create_tag()
        for self.debug_iteration in range(1, self.max_debug_iterations + 1):
            code_and_output = self._get_and_run_code()
            if code_and_output is not None:
                return code_and_output
        return None
