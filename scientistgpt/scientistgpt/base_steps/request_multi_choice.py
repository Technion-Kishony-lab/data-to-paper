from dataclasses import dataclass
from typing import Tuple, Optional

from scientistgpt.utils import dedent_triple_quote_str

from .base_products_conversers import BaseProductsGPT
from .exceptions import FailedCreatingProductException
from ..utils.replacer import with_attribute_replacement


@dataclass
class BaseMultiChoiceProductsGPT(BaseProductsGPT):
    """
    A base class for asking ChatGPT to choose between multiple options.
    """

    max_regenerating_multi_choice_response: int = 4

    multi_choice_question: str = 'Please choose one of the following options:\n' \
                                 '1. Looks good.\n' \
                                 '2. Something is wrong.\n'

    choice_instructions: str = dedent_triple_quote_str("""
        Answer with just a single character, designating the option you choose {possible_choices}.
        """)

    multi_choice_question_tag: str = None

    possible_choices: Tuple[str, ...] = ('1', '2')

    CHATGPT_PARAMETERS = {'temperature': 0.0, 'max_tokens': 10}

    def _get_chosen_choice_from_response(self, response: str) -> Optional[str]:
        choices_in_response = [choice for choice in self.possible_choices if choice in response]
        if len(choices_in_response) == 1:
            return choices_in_response[0]
        return None

    def _get_chosen_choice(self, regenerate: bool = False) -> str:
        if regenerate:
            response = self.conversation_manager.regenerate_previous_response()
        else:
            response = self.apply_get_and_append_assistant_message(**self.CHATGPT_PARAMETERS)
        return self._get_chosen_choice_from_response(response)

    @with_attribute_replacement
    def get_chosen_option(self) -> str:
        self.apply_append_user_message(
            content=self.multi_choice_question + '\n' + self.choice_instructions,
            tag=self.multi_choice_question_tag)
        chosen_choice = self._get_chosen_choice()
        if chosen_choice is not None:
            return chosen_choice
        self.apply_append_user_message(self.choice_instructions)

        for num_tries in range(self.max_regenerating_multi_choice_response):
            chosen_choice = self._get_chosen_choice(regenerate=num_tries > 0)
            if chosen_choice is not None:
                return chosen_choice
        raise FailedCreatingProductException()

