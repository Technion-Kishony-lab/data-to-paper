import copy
from typing import Optional, List

from scientistgpt.proceed_retract import FuncAndRetractions, RunPlan
from scientistgpt.exceptions import FailedDebuggingException
from scientistgpt.conversation import Conversation
from scientistgpt.utils.text_utils import format_str, print_red

from .debugger_gpt import DebuggerGPT
from .converser_gpt import ConverserGPT

GPT_SCRIPT_FILENAME = 'gpt_analysis'


class ScientistGPT(ConverserGPT):
    """
    Create a conversation with chatgpt with interactive analysis of data.

    The user needs to provide:
    data_description: a comprehensive description of the data files available for the project.
                      It is recommended that this description includes a few-line header of each file.
    goal_description: a description of the goal of the analysis.

    ScientistGPT will interact with chatgpt to create analysis code and interpret the results.
    """

    # NOTE: For the text of gpt prompt, we use the triple-quote notation because it elegantly takes care of newlines
    #       and can be integrated within the class functions.
    #       Any preceding spaces are removed with format_str().
    #       Note though that this notation does not work with f-string formatting especially when the dynamically
    #       added text includes multiple lines.
    #       We therefore use instead the triple-quote with the .format() notation to get a dynamic, yet structured and
    #       readable, multi-line text.
    def __init__(self,
                 run_plan: List[FuncAndRetractions] = None,
                 conversation: Optional[Conversation] = None,
                 data_description: Optional[str] = None,
                 goal_description: Optional[str] = None,
                 ):
        super().__init__(run_plan, conversation)
        self.data_description = data_description
        self.goal_description = goal_description
        self._run_code_attempt = 0

    def add_data_description(self):
        prompt = format_str("""
            We have the following data files:

            {}
            """).format(self.data_description)
        self.conversation.append_user_message(prompt)
        self.conversation.append_assistant_message('ok')

    def add_goal_description(self):
        prompt = self.goal_description
        self.conversation.append_user_message(prompt)
        self.conversation.append_assistant_message('ok')

    def request_analysis_plan(self):
        prompt = format_str("""
            Suggest a data analysis plan to achieve the specified goal.
            """)
        self.conversation.append_user_message(prompt)
        return self.conversation.get_response_from_chatgpt()

    def request_analysis_code(self):
        prompt = format_str(f"""
            Write a complete Python code to perform the analysis you suggested.
            The output of the code should be a text file named `{self.OUTPUT_FILENAME}`.
            """)
        self.conversation.append_user_message(prompt)

    def run_gpt_code_and_add_output_to_conversation(self):
        print_red('Transfer control to DebuggerGPT to debug and get a functional code ...')
        self._run_code_attempt += 1
        debugger = DebuggerGPT(conversation=copy.deepcopy(self.conversation),
                               script_file=f"{GPT_SCRIPT_FILENAME}_{self._run_code_attempt}",
                               new_file_for_each_try=True)
        result = debugger.debug_and_run_code()
        self.conversation = debugger.conversation
        print_red("Code ran successfully! Let's see what chatgpt think of the results ...")

        prompt = format_str("""
            I ran your code. Here is the content of the output file ({}):
            ```
            {}
            ```

            Do these results make sense, or do you suspect any problems, bugs or artifacts in the analysis code?

            If you suspect a problem, please provide a new full compete code which correctly resolves the problem.
            """).format(self.OUTPUT_FILENAME, result)
        self.conversation.append_user_message(prompt)

    def get_gpt_response_to_analysis(self):
        return self.conversation.get_response_from_chatgpt()


upon_code_failure = [1, 1, 2, 1, 1]
# This means that if the code failed despite debugging attempts (as defined by DebuggerGPT),
# we go back 1 step (to request_analysis_code). If it fails again, we go back again 1 step. If it then fails for
# the third time, we go back 2 steps (to request_analysis_plan, thus revising the whole plan).
# We then try again the same process on the new plan (going back 1 step for two failures [1, 1]).
# If it still fails, we end and raise an exception.

ScientistGPT_ANALYSIS_PLAN: RunPlan = [
    FuncAndRetractions('initialize_conversation', (), []),
    FuncAndRetractions('add_data_description', (), []),
    FuncAndRetractions('add_goal_description', (), []),
    FuncAndRetractions('request_analysis_plan', (), []),
    FuncAndRetractions('request_analysis_code', (), []),
    FuncAndRetractions('run_gpt_code_and_add_output_to_conversation', FailedDebuggingException, upon_code_failure),
    FuncAndRetractions('get_gpt_response_to_analysis', (), []),
]
