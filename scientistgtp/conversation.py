import openai

from typing import Dict, List

# Set up the OpenAI API client
openai.api_key = "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"

# Set up the model and prompt
model_engine = "gpt-3.5-turbo"


class Conversation(list):

    @staticmethod
    def print_message(message: str, should_print: bool = True):
        if should_print:
            print('-----------------')
            print('\n' + message + '\n')

    def append_message(self, role: str, message: str, should_print: bool = False):
        self.append({'role': role, 'content': message})
        self.print_message(message, should_print)

    def get_response(self,
                     should_print: bool = True,
                     should_append: bool = True) -> str:
        response = openai.ChatCompletion.create(
            model=model_engine,
            messages=self,
        )
        response_message = response['choices'][0]['message']['content']
        if should_append:
            self.append_message('assistant', response_message)
        self.print_message(response_message, should_print)
        return response_message