from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, Union

from scientistgpt import Message, Role
from scientistgpt.base_steps.converser import Converser
from scientistgpt.base_steps.exceptions import FailedCreatingProductException
from scientistgpt.utils.replacer import Replacer, StrOrTextFormat


@dataclass
class SelfResponseError(Exception):
    """
    Exception raised when the response to a request for a latex section is not acceptable.
    """
    error_message: StrOrTextFormat = None

    def __str__(self):
        return self.error_message


class NoResponse:
    pass


@dataclass
class ResultConverser(Converser):

    performer: str = 'scientist'

    # goal_noun: the desired output of the conversation (expressed as a singular noun).
    goal_noun: str = 'one-paragraph summary on the solar system'

    # goal_verb: a verb applied to achieve the goal, like 'write', 'draw', 'build', 'code', etc.
    goal_verb: str = 'write'

    # *** Properties that are more generic (adjust only if needed) ***

    system_prompt: str = "You are a {performer} who needs to {goal_verb} a {goal_noun}."

    user_initiation_prompt: str = "Please {goal_verb} a {goal_noun}."

    max_valid_response_iterations: int = 4

    response_to_self_error: str = "{}"
    # {} is the error message. sub-classes can add additional text you want to send to self upon error in its response.

    # Output:
    returned_result: Any = field(default_factory=NoResponse)

    def initialize_conversation_if_needed(self):
        super().initialize_conversation_if_needed()
        self._pre_populate_background()

    def _pre_populate_background(self):
        """
        Add background messages to the two conversations to set them ready for the cycle.
        """
        if self.user_initiation_prompt:
            self.apply_append_user_message(self.user_initiation_prompt, tag='user_initiation_prompt')

    def _raise_self_response_error(self, error_message: str):
        """
        Raise a SelfResponseError with the given error message.
        """
        raise SelfResponseError(error_message)

    def _check_and_extract_result_from_self_response(self, response: str):
        """
        Check the response from self.
        Extract any needed information into returned_result.
        If the there are errors that require self to revise the response, raise an SelfResponseError describing
        the problem.
        """
        self.returned_result = response

    def _alter_self_response(self, response: str) -> str:
        """
        Alter the response from self when posted to web.
        This method also used to alter the response to send to other in dual_conversation.
        """
        return response

    def _get_fresh_looking_response(self, response) -> str:
        """
        Convert the response to a response that looks as if it was the first response.
        """
        return response

    def _iterate_until_valid_response(self, alter_web_response: bool = False) -> Optional[str]:
        """
        Iterate until we get a valid response from self.
        If we started with a pre-existing self response which was valid, we return it.
        Otherwise, we return the valid message that we got after iterating.
        If we fail to get a valid response after max_valid_response_iterations, return None.
        """
        self_message = None
        for _ in range(self.max_valid_response_iterations):
            # to allow starting either before or after the first self response:
            is_preexisting_self_response = True
            try:
                self_response = self.conversation.get_last_response()
                # We are starting after the first self response
            except ValueError:
                # We are starting before the first self response
                is_preexisting_self_response = False
                self_message = self.apply_get_and_append_assistant_message(web_conversation_name=None)
                self_response = self_message.content

            # check if the response is valid:
            response_error = None
            try:
                self._check_and_extract_result_from_self_response(self_response)
            except SelfResponseError as e:
                response_error = e

            if not is_preexisting_self_response:
                self.apply_append_surrogate_message(
                    content=(self_response if response_error or not alter_web_response
                             else self._alter_self_response(self_response)),
                    conversation_name=None, context=self_message.context)
            if not response_error:
                return self_response

            # The response is not valid.
            self.apply_append_user_message(
                Replacer(self, self.response_to_self_error, args=(response_error.error_message,)), tag='error')
        else:
            return None

    def run_and_get_valid_result(self):
        self._iterate_until_valid_response()
        return self.get_valid_result()

    def get_valid_result(self):
        if isinstance(self.returned_result, NoResponse):
            raise FailedCreatingProductException()
        return self.returned_result
