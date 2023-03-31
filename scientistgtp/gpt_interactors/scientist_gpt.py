import copy
from typing import Optional, List

from scientistgtp.proceed_retract import FuncAndRetractions, RunPlan
from scientistgtp.exceptions import RunCodeException, DebuggingFailedException
from scientistgtp.conversation import Conversation
from scientistgtp.utils import format_str

from .debugger_gpt import DebuggerGPT
from .converser_gpt import ConverserGPT


class ScientistGTP(ConverserGPT):
    def __init__(self,
                 run_plan: List[FuncAndRetractions] = None,
                 conversation: Optional[Conversation] = None,
                 data_description: Optional[str] = None,
                 goal_description: Optional[str] = None,
                 ):
        super().__init__(run_plan, conversation)
        self.data_description = data_description
        self.goal_description = goal_description

    def add_data_description(self):
        prompt = format_str(f"""
            We have the following data files:

            {self.data_description}
            """)
        self.conversation.append_user_message(prompt)
        self.conversation.append_assistant_message('ok')

    def add_goal_description(self):
        prompt = format_str(f"""
            {self.goal_description}
            """)
        self.conversation.append_user_message(prompt)
        self.conversation.append_assistant_message('ok')

    def request_analysis_plan(self):
        prompt = format_str(f"""
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
        debugger = DebuggerGPT(conversation=copy.deepcopy(self.conversation))
        result = debugger.debug_and_run_code()
        self.conversation = debugger.conversation

        prompt = format_str(f"""
            I ran your code. Here is the content of the output file ({self.OUTPUT_FILENAME}):
            ```
            {result}
            ```
            
            Do these results make sense, or do you suspect any problems, bugs or artifacts in the analysis code?
            
            If you suspect a problem, please provide a new full compete code which correctly resolves the problem.
            """)
        self.conversation.append_user_message(prompt)

    def get_gpt_response_to_analysis(self):
        return self.conversation.get_response_from_chatgpt()



ScientistGTP_ANALYSIS_PLAN: RunPlan = [
    FuncAndRetractions('initialize_conversation', (), []),
    FuncAndRetractions('add_data_description', (), []),
    FuncAndRetractions('add_goal_description', (), []),
    FuncAndRetractions('request_analysis_plan', (), []),
    FuncAndRetractions('request_analysis_code', (), []),
    FuncAndRetractions('run_gpt_code_and_add_output_to_conversation', DebuggingFailedException, [1, 1, 2, 1, 1, 2]),
    FuncAndRetractions('get_gpt_response_to_analysis', (), []),
]

