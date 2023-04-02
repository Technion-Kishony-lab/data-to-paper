import os
from typing import List, Optional

import colorama

from scientistgpt.code_runner import CodeRunner
from scientistgpt.exceptions import FailedExtractingCode, FailedRunningCode, FailedLoadingOutput, \
    FailedDebuggingException
from scientistgpt.env import SUPPORTED_PACKAGES
from scientistgpt.utils.text_utils import format_str, print_red
from scientistgpt.conversation import Conversation
from scientistgpt.proceed_retract import FuncAndRetractions

from .converser_gpt import ConverserGPT

MAX_DEBUGGING_ATTEMPTS = 3
MAX_ITERATIONS_PER_ATTEMPT = 5


class DebuggerGPT(ConverserGPT):
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

    def __init__(self,
                 run_plan: List[FuncAndRetractions] = None,
                 conversation: Optional[Conversation] = None,
                 script_file: str = None,
                 new_file_for_each_try: bool = True,
                 ):
        super().__init__(run_plan, conversation)
        self.script_file = script_file
        self.new_file_for_each_try = new_file_for_each_try
        self._debug_iteration = 0

    def _run_code_from_last_response(self):
        self._debug_iteration += 1
        script_file = self.script_file
        if self.new_file_for_each_try:
            script_file += f'_{self._debug_iteration}'
        result = CodeRunner(response=self.conversation.get_last_response(),
                            output_file=self.OUTPUT_FILENAME,
                            script_file=script_file,
                            ).run_code()
        os.rename(self.OUTPUT_FILENAME, script_file + '.txt')
        return result

    def _specify_allowed_packages(self, error_message: str):
        prompt = format_str("""
            I ran the code and got the following error message:
            ```
            {}
            ```
            Please rewrite the code using only these packages: {}. 
            """).format(error_message, ', '.join(SUPPORTED_PACKAGES))
        self.conversation.append_user_message(prompt)

    def _specify_error_message(self, error_message: str):
        prompt = format_str("""
            I ran the code and got the following error message:
            ```
            {}
            ```
            Please rewrite the complete code again with this error corrected. 
            """).format(error_message)
        self.conversation.append_user_message(prompt)

    def _specify_missing_output(self):
        prompt = format_str("""
            I ran the code, but it didn't generate the desired output file ({}).
            Please rewrite the complete code again with this error corrected. 
            """).format(self.OUTPUT_FILENAME)
        self.conversation.append_user_message(prompt)

    def _specify_timeout(self):
        prompt = format_str("""
            I ran the code, but it just ran forever...
            Please fix and rewrite the complete code again so that it doesn't get stuck. 
            """)
        self.conversation.append_user_message(prompt)

    def debug_and_run_code(self):
        """
        Interact with chatgpt until getting a functional code that can run locally and produce desired output file.
        :return: content of the file produced by the gpt code.
        """

        self.save_current_state_by_name('initial')

        for debug_attempt in range(MAX_DEBUGGING_ATTEMPTS):
            self.reset_state_to('initial')
            if debug_attempt > 0:
                print_red(f'DEBUGGER: Debugging failed. Restarting chatgpt communication from scratch.'
                          f'({debug_attempt + 1}/{MAX_DEBUGGING_ATTEMPTS}).')
            for iteration_num in range(MAX_ITERATIONS_PER_ATTEMPT):
                self.conversation.get_response_from_chatgpt()
                try:
                    result = self._run_code_from_last_response()
                except FailedExtractingCode:
                    # no code, or multiple code snippets, were found.
                    # remove the last gpt response to re-generate:
                    self.conversation.pop(-1)
                    print_red('DEBUGGER: Failed extracting code from gpt response. Regenerating response...')
                except FailedRunningCode as e:
                    if isinstance(e.exception, ImportError):
                        # chatgpt tried using a package we do not support
                        print_red('DEBUGGER: ImportError detected in gpt code. Notifying chatgpt...')
                        self._specify_allowed_packages(str(e.exception))
                    elif isinstance(e.exception, TimeoutError):
                        # code took too long to run
                        print_red('DEBUGGER: GPT code has timed out. Notifying chatgpt...')
                        self._specify_timeout()
                    else:
                        # the code failed on other errors.
                        # indicate error message to chatgpt.
                        print_red('DEBUGGER: Runtime exception in GPT code. Notifying chatgpt...')
                        self._specify_error_message(e.get_traceback_message())
                except FailedLoadingOutput:
                    # Code ran, but the output file was not created.
                    print_red('DEBUGGER: GPT code completed successfully, '
                              'but output file not created. Notifying chatgpt...')
                    self._specify_missing_output()
                except Exception:
                    raise
                else:
                    # The code ran just fine.
                    print_red("DEBUGGER: GPT code completed successfully. Returning results to ScientistGPT.")
                    return result
        raise FailedDebuggingException()
