import os
from dataclasses import dataclass
from typing import Optional

from scientistgpt.run_gpt_code.code_runner import CodeRunner, CodeAndOutput
from scientistgpt.env import SUPPORTED_PACKAGES
from scientistgpt.utils import dedent_triple_quote_str
from scientistgpt.run_gpt_code.exceptions import FailedExtractingCode, FailedRunningCode, FailedLoadingOutput

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

    def _run_code_from_response(self, response: str, debug_iteration: int) -> CodeAndOutput:
        script_file = f'{self.gpt_script_filename}_{debug_iteration}'
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
            comment='ImportError detected in gpt code. Notifying chatgpt...')

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
            comment='FileNotFound detected in gpt code. Notifying chatgpt...')

    def _specify_error_message(self, error_message: str):
        self.conversation_manager.append_user_message(
            content=dedent_triple_quote_str("""
            I ran the code and got the following error message:
            ```
            {}
            ```
            Please rewrite the complete code again with this error corrected. 
            """).format(error_message),
            comment='Runtime exception in GPT code. Notifying chatgpt...')

    def _specify_missing_output(self):
        self.conversation_manager.append_user_message(
            content=dedent_triple_quote_str("""
            I ran the code, but it didn't generate the desired output file ({}).
            Please rewrite the complete code again with this error corrected. 
            """).format(self.output_filename),
            comment='GPT code completed successfully, but output file not created. Notifying chatgpt...')

    def _specify_timeout(self):
        self.conversation_manager.append_user_message(
            content=dedent_triple_quote_str("""
            I ran the code, but it just ran forever...
            Please fix and rewrite the complete code again so that it doesn't get stuck. 
            """),
            comment='GPT code has timed out. Notifying chatgpt...')

    def _get_and_run_code(self, debug_iteration: int) -> Optional[CodeAndOutput]:
        """
        Get a code from chatgpt, run it and return code and result.
        If the code fails, notify chatgpt and return None.
        """

        response = self.conversation_manager.get_and_append_assistant_message()
        try:
            code_and_output = self._run_code_from_response(response, debug_iteration=debug_iteration)
        except FailedExtractingCode:
            self.conversation_manager.delete_messages(
                message_designation=-1,  # last message
                comment='Failed extracting code from gpt response. Delete response and regenerate...'
            )
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
        return None  # code failed

    def run_debugging(self) -> Optional[CodeAndOutput]:
        """
        Run the debugging process.
        If debugging did not converge to a running code within the max_debug_iterations, return None.
        Otherwise, return the code and output.
        """
        self.conversation_manager.append_commenter_message(
            "Starting a debugging process.")

        for debug_iteration in range(self.max_debug_iterations):
            code_and_output = self._get_and_run_code(debug_iteration)
            if code_and_output is not None:
                return code_and_output
        return None
