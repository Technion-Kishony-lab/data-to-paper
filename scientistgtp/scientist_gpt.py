import copy
from typing import Optional, List, Callable, Any, Tuple, NamedTuple

from .conversation import Conversation, Role
from .code_runner import CodeRunner
from .exceptions import RunCodeException

OUTPUT_FILENAME = 'results.txt'


class ScientistGTP:
    def __init__(self, data_description: str, goal_description: str):
        self.data_description = data_description
        self.goal_description = goal_description
        self.conversation: Optional[Conversation] = None
        self.data_analysis_plan: Optional[str] = None

    def initialize_conversation(self):
        self.conversation = Conversation()
        self.conversation.append_message(Role.SYSTEM, 'You are a helpful scientist.')

    def add_data_description(self):
        self.conversation.append_message(Role.USER, 'We have the following data files:\n\n' + self.data_description)

    def add_goal_description(self):
        self.conversation.append_message(Role.USER, self.goal_description)

    def request_analysis_plan(self):
        self.initialize_conversation()
        self.add_data_description()
        self.add_goal_description()
        self.conversation.append_message(Role.USER, 'Suggest a data analysis plan to achieve the specified goal.')
        self.data_analysis_plan = self.conversation.get_response()
        return self.data_analysis_plan

    def request_analysis_code(self):
        self.conversation.append_message(Role.USER,
                                         f'Write a complete Python code to perform the analysis you suggested.\n'
                                         f'The output of the code should be a text file named `{OUTPUT_FILENAME}`.')

    def run_analysis_code(self):
        self.request_analysis_code()
        analysis_code_response = self.conversation.get_response(should_append=False)
        result = CodeRunner(response=analysis_code_response, output_file=OUTPUT_FILENAME)
        self.conversation.append_message(Role.ASSISTANT, analysis_code_response)

    def analyze_and_write_paper(self):
        self.request_analysis_plan()


'''
request analysis plan
request and run code

'''
