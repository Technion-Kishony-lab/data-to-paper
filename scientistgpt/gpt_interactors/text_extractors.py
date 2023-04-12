from dataclasses import dataclass

from scientistgpt.conversation.actions import get_name_with_new_number

from .converser_gpt import ConverserGPT


@dataclass
class TextExtractorGPT(ConverserGPT):
    """
    Interact with chatgpt to extract specific text from a response.
    """

    # override the default system prompt:
    system_prompt: str = 'You are a helpful assistant.'

    text: str = None
    """
    A text response, typically from another chatgpt conversation, from which to extract text.
    """

    description_of_text_to_extract: str = None
    """
    A description of the text to extract, e.g. 'the first sentence'.
    """

    max_number_of_attempts: int = 3

    def extract_text(self):
        """
        Extract text from the response.
        """

        self.initialize_conversation_if_needed()
        self.conversation_manager.append_user_message(
            f'Below is a triple-quoted text, from which you need to extract {self.description_of_text_to_extract}.\n'
            f'Please provide the extracted text within a triple-quoted string.\n\n'
            f'Here is my text:\n\n'
            f'"""{self.text}"""\n\n')

        for attempt_num in range(self.max_number_of_attempts):
            response = self.conversation_manager.get_and_append_assistant_message()
            try:
                return self.extract_triplet_quoted_text(response)
            except ValueError:
                self.conversation_manager.append_user_message(
                    f'You did not extract the {self.description_of_text_to_extract} correctly. \n'
                    f'Please try again making sure the extracted text is flanked by triple quotes, \n'
                    f'like this """extracted text""".', tag='explicit_instruction')
        raise ValueError(f'Could not extract text after {self.max_number_of_attempts} attempts.')

    @staticmethod
    def extract_triplet_quoted_text(text):
        """
        Extract the text between triple-quoted strings.
        """
        if text.count('"""') != 2:
            raise ValueError(f'Expected exactly two triple-quoted strings.')
        return text.split('"""')[1]


def extract_analysis_plan_from_response(response: str, max_number_of_attempts: int = 3,
                                        base_conversation_name: str = 'extract_analysis_plan') -> str:
    """
    Extract the analysis plan from a response.
    """
    return TextExtractorGPT(
        text=response,
        description_of_text_to_extract='analysis plan',
        max_number_of_attempts=max_number_of_attempts,
        system_prompt='You are a helpful assistant.',
        conversation_name=get_name_with_new_number(base_conversation_name),
    ).extract_text()
