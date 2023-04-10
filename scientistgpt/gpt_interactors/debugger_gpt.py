import os
from dataclasses import dataclass

from scientistgpt.code_runner import CodeRunner
from scientistgpt.env import SUPPORTED_PACKAGES
from scientistgpt.utils.text_utils import dedent_triple_quote_str
from scientistgpt.exceptions import FailedExtractingCode, FailedRunningCode, FailedLoadingOutput, \
    FailedDebuggingException

from .converser_gpt import CodeWritingGPT

MAX_DEBUGGING_ATTEMPTS = 3
MAX_ITERATIONS_PER_ATTEMPT = 2
MAX_EXEC_TIME = 900


@dataclass
class DebuggerGPT(CodeWritingGPT):
    """
    Interact with chatgpt to debug a code that needs to create an output file.

    Starting with a conversation which ends with a code-request from the user, DebuggerGPT interacts with chatgpt to
    enhance the code until it runs properly and creates a desired output file.

    Interactions with chatgpt include adequate reporting of:
    * missing packages
    * syntax errors
    * runtime exceptions
    * too long runs (timeout)
    * output file not created
    """

    agent: str = 'DEBUGGER'
    _debug_iteration: int = 0

    def _run_code_from_response(self, response: str):
        self._debug_iteration += 1
        script_file = f'{self.gpt_script_filename}_{self._debug_iteration}'
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

    def debug_and_run_code(self):
        """
        Interact with chatgpt until getting a functional code that can run locally and produce desired output file.
        :return: content of the file produced by the gpt code.
        """

        start_tag = self.conversation[-1].tag
        assert start_tag is not None
        for debug_attempt in range(MAX_DEBUGGING_ATTEMPTS):
            self.conversation_manager.reset_back_to_tag(start_tag)
            if debug_attempt > 0:
                self.conversation_manager.append_commenter_message(
                    f'Debugging failed. Restarting debugging from scratch '
                    f'({debug_attempt + 1}/{MAX_DEBUGGING_ATTEMPTS}).')
            for iteration_num in range(MAX_ITERATIONS_PER_ATTEMPT):
                response = self.conversation_manager.get_and_append_assistant_message()
                try:
                    result = self._run_code_from_response(response)
                except FailedExtractingCode:
                    self.conversation_manager.delete_messages(
                        message_designation=-1,  # last message
                        comment='Failed extracting code from gpt response. Delete response and retry...'
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
                        # the code tried to load file that we do not have.
                        self._specify_file_not_found(str(e.exception))
                    except Exception:
                        # the code failed on other errors.
                        # indicate error message to chatgpt.
                        self._specify_error_message(e.get_traceback_message())
                except FailedLoadingOutput:
                    # Code ran, but the output file was not created.
                    self._specify_missing_output()
                except Exception:
                    raise
                else:
                    # The code ran just fine.
                    self.conversation_manager.append_commenter_message(
                        "GPT code completed successfully. Returning results to MentorGPT.")
                    return result
        raise FailedDebuggingException()
