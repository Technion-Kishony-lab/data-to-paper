from dataclasses import dataclass
from typing import Optional

from conversation import Conversation
from run_code import RunCode, RunCoodeException


OUTPUT_FILENAME = 'results.txt'


class ScientistGTP:
    def __init__(self, data_description: str, goal_description: str):
        self.data_description = data_description
        self.goal_description = goal_description
        self.conversation: Optional[Conversation] = None
        self.data_analysis_plan: Optional[str] = None

    def initialize_conversation(self):
        self.conversation = Conversation()
        self.conversation.append_message('system', 'You are a helpful scientist.')

    def add_data_description(self):
        self.conversation.append_message('user', 'We have the following data files:\n\n' + self.data_description)

    def add_goal_description(self):
        self.conversation.append_message('user', self.goal_description)

    def request_analysis_plan(self):
        self.initialize_conversation()
        self.add_data_description()
        self.add_goal_description()
        self.conversation.append_message('user', 'Suggest a data analysis plan to achieve the specified goal.')
        self.data_analysis_plan = self.conversation.get_response()
        return self.data_analysis_plan

    def request_analysis_code(self):
        self.conversation.append_message('user',
                                         f'Write a complete Python code to perform the analysis you suggested.\n'
                                         f'The output of the code should be a text file named `{OUTPUT_FILENAME}`.')

    def run_analysis_code(self):
        result = None
        counter = 4
        while counter > 0 and result is None:
            counter -= 1
            analysis_code_response = self.conversation.get_response()
            try:
                result = RunCode(response=analysis_code_response, output_file=OUTPUT_FILENAME)
            except RunCoodeException:
                pass

        if result is None:
            raise RuntimeError()

    def analyze_and_write_paper(self):
        self.request_analysis_plan()

