import copy
from typing import Optional, List

from scientistgpt.proceed_retract import FuncAndRetractions, RunPlan
from scientistgpt.exceptions import FailedDebuggingException
from scientistgpt.conversation import Conversation
from scientistgpt.utils.text_utils import format_str, print_red
from scientistgpt.env import SUPPORTED_PACKAGES
from .reviewer_gpt import ReviewerGPT

from .debugger_gpt import DebuggerGPT
from .converser_gpt import ConverserGPT

GPT_SCRIPT_FILENAME = 'gpt_analysis'
MAX_ANALYSIS_REVISIONS = 2

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
                 analysis_plan: Optional[str] = None,
                 ):
        super().__init__(run_plan, conversation)
        self.data_description = data_description
        self.goal_description = goal_description
        self.analysis_plan = analysis_plan
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
        reply = self.conversation.get_response_from_chatgpt()
        self.analysis_plan = self.conversation.get_last_response()
        return reply

    def request_analysis_code(self):
        prompt = format_str(f"""
            Write a complete Python code to perform the analysis you suggested.
            Use only the packages: {SUPPORTED_PACKAGES} to perform the analysis.
            The output of the code should be a text file named `{self.OUTPUT_FILENAME}`.
            The plots should be saved as image files and not displayed to screen.
            """)
        self.conversation.append_user_message(prompt)

    def review_analysis_plan(self):
        print_red('Ask ReviewerGPT to find flaws within the plan  ...')
        reviewer = ReviewerGPT(conversation=copy.deepcopy(self.conversation))
        result = reviewer.review_plan(self.analysis_plan)
        self.analysis_plan = result
        # replace the last message with the updated plan
        self.conversation.delete_last_response()
        self.conversation.append_assistant_message(self.analysis_plan)

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
            
            You are obliged to choose one of the following options:
            1. I am satisfied with the analysis and the results, I am ready to write a paper about them.
            2. I need to write additional code the code and try again before writing a paper.
            
            Answer with the number of the option you choose only, e.g. "1".
            """).format(self.OUTPUT_FILENAME, result)
        self.conversation.append_user_message(prompt)

    def get_gpt_response_to_analysis(self):
        analysis_revises = 0
        while analysis_revises < MAX_ANALYSIS_REVISIONS:
            result = self.conversation.get_response_from_chatgpt(should_append=False)
            if result == '1':
                break

            if result == '2':
                prompt = format_str("""
                Write additional code to improve the analysis and try again. write any additional results to the output file.
                """)
                self.conversation.append_user_message(prompt)
                self.conversation.get_response_from_chatgpt()
                self.run_gpt_code_and_add_output_to_conversation()
            analysis_revises += 1

def write_paper(self):
    # TODO: take data description, goal description, analysis plan and code and results and create a paper
    prompt = format_str("""
    Write the paper, write abstract, introduction, methods, results, discussion and acknowledgments.
    In addition you are required to state where to add the figure of you created during the analysis by using
    FIGURE@#@ name_of_figure @#@ where name_of_figure is the name of the figure you want to enter.
    """)
    self.conversation.append_user_message(prompt)
    self.conversation.get_response_from_chatgpt()


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
    FuncAndRetractions('review_analysis_plan', (), []),
    FuncAndRetractions('request_analysis_code', (), []),
    FuncAndRetractions('run_gpt_code_and_add_output_to_conversation', FailedDebuggingException, upon_code_failure),
    FuncAndRetractions('get_gpt_response_to_analysis', (), []),

]
