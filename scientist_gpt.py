import openai

from typing import Dict, List

# Set up the OpenAI API client
openai.api_key = "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"

# Set up the model and prompt
model_engine = "gpt-3.5-turbo"

# Conversation = List[Dict[str, str]]


class Conversation(list):
    def append_message(self, role:str, message:str):
        self.append({'role': role, 'content':message})

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
        if should_print:
            print('\n' + response_message + '\n')
        return response_message


conversation = Conversation()
conversation.append_message('system', 'You are a helpful scientist.')

data_description = """
a dataframe (patient_records) containing electronic health records. 
Each line indicates a diagnostic event where a given patient was diagnosed with a specific medical diagnostic, 
indicated as an ICD10 code. 
The dataframe has 4 columns: Patient ID (id), Gender (gender), Date (date), Diagnostic ICD10 code (ICD10). 
There are about 1 million lines. 
"""

goal_description = """
I am interested to see if certain diagnostic codes have different "clinical meaning" for males vs females. 

Can you suggest an analysis that will identify gender-context-dependent diagnostic codes, namely codes that are used at different clinical context in men versus women? 

For example, a code X is gender-context-dependent if it is typically found in proximity to code Y in female and to a different code Z in males. 

Note that code X can be gender-context-dependent, despite being used in similar frequency in males and in females. 
"""

conversation.append_message('user', data_description)
conversation.append_message('user', goal_description)

conversation.get_response()

conversation.append_message('user', 'Write a Python code to perform the analysis you suggested')

conversation.get_response()
