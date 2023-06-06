from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from scientistgpt.base_steps.converser import Converser
from scientistgpt.base_steps.exceptions import FailedCreatingProductException
from scientistgpt.conversation.message_designation import RangeMessageDesignation
from scientistgpt.env import MAX_MODEL_ENGINE
from scientistgpt.utils.highlighted_text import print_red
from scientistgpt.utils.replacer import Replacer, StrOrTextFormat, format_value


class Rewind(Enum):
    """
    An enum for the different ways to rewind the conversation upon invalid response.

    For example:

    (1) user initiation prompt

    (2) here is the code
    (3) you have an error

    (4) Here is the revised code
    (5) you have an error in the revised code

    (6) Here is the revised-revised code
    (7) you have an error in the revised-revised code

    REGENERATE: delete (6)-(7)
    RESTART: delete (2)-(7)
    REPOST_AS_FRESH: delete (2)-(5) and change (6) to look fresh
    ACCUMULATE: do nothing
    AS_FIRST_CORRECTION: delete (4)-(5)
    DELETE_ALL: delete (1)-(7)
    """

    REGENERATE = 'regenerate'
    # regenerate the last response

    RESTART = 'restart'
    # deleted all iterations and get a fresh response

    REPOST_AS_FRESH = 'repost_as_fresh'
    # delete all previous iterations and modify and post the current response as if it was first iteration

    ACCUMULATE = 'accumulate'
    # just normally add the current response and the feedback

    AS_FIRST_CORRECTION = 'as_first_correction'
    # delete any previous erroneous responses, making the current response the first correction

    DELETE_ALL = 'delete_all'
    # delete all previous responses including the original user initiation prompt


@dataclass
class SelfResponseError(Exception):
    """
    Exception raised when the response to a request for a latex section is not acceptable.
    """
    error_message: StrOrTextFormat = None
    rewind: Rewind = None
    bump_model: bool = False

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

    max_valid_response_iterations: int = 7

    response_to_self_error: str = "{}"
    # {} is the error message. subclasses can add additional text you want to send to self upon error in its response.

    rewind_after_getting_a_valid_response: Optional[Rewind] = None
    # Can be:
    # DELETE_ALL: leave the conversation as if the exchange never happened
    # REPOST_AS_FRESH: rewind back to right after the user initiation prompt and post the last response as fresh
    # ACCUMULATE (all `None`): do not do anything. the exchange is left as is.

    _conversation_len_before_first_response: int = None
    _self_response_iteration_count: int = 0

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
            self.apply_append_user_message(self.user_initiation_prompt)

    def _raise_self_response_error(self, error_message: str, rewind: Rewind = Rewind.ACCUMULATE,
                                   bump_model: bool = False):
        """
        Raise a SelfResponseError with the given error message and instructions for how to rewind the conversation.
        """
        raise SelfResponseError(format_value(self, error_message), rewind=rewind, bump_model=bump_model)

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
        This is called after _check_and_extract_result_from_self_response, so the method can use `returned_result`.
        """
        return response

    def _rewind_conversation_to_first_response(self, offset: int = 0, last: int = -1, start: int = None):
        """
        Rewind the conversation to the first response + offset.
        offset=0 means that we delete all messages including the first response.
        """
        if start is None:
            start = self._conversation_len_before_first_response
        self.apply_delete_messages(
            RangeMessageDesignation.from_(start + offset, last))

    def _iterate_until_valid_response(self, alter_web_response: bool = False) -> Optional[str]:
        """
        Iterate until we get a valid response from self.
        If we started with a pre-existing self response which was valid, we return it.
        Otherwise, we return the valid message that we got after iterating.
        If we fail to get a valid response after max_valid_response_iterations, return None.
        """
        self._conversation_len_before_first_response = len(self.conversation)
        self_message = None
        while self._self_response_iteration_count < self.max_valid_response_iterations:
            self._self_response_iteration_count += 1
            # to allow starting either before or after the first self response:
            is_preexisting_self_response = True
            try:
                self_response = self.conversation.get_last_response()
                # We are starting after the first self response
            except ValueError:
                # We are starting before the first self response
                is_preexisting_self_response = False

            if not is_preexisting_self_response:
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

            if response_error and response_error.rewind == Rewind.REPOST_AS_FRESH \
                    or not response_error and self.rewind_after_getting_a_valid_response == Rewind.REPOST_AS_FRESH:
                self._rewind_conversation_to_first_response()
                self.apply_append_surrogate_message(self._get_fresh_looking_response(self_response))

            if not response_error:
                if self.rewind_after_getting_a_valid_response == Rewind.DELETE_ALL:
                    self._rewind_conversation_to_first_response(-1)  # delete including the user initiation prompt
                return self_response

            # The response is not valid
            if response_error.bump_model and self.model_engine < MAX_MODEL_ENGINE:
                self.apply_append_user_message(
                    f"You seem totally drunk. Let's Bump you to {MAX_MODEL_ENGINE} and try again...",
                    conversation_name=None)  # web only
                print_red(f"You seem totally drunk. Let's Bump you to {MAX_MODEL_ENGINE} and try again...")
                self.model_engine = MAX_MODEL_ENGINE
            self.apply_append_user_message(
                Replacer(self, self.response_to_self_error, args=(response_error.error_message,)))
            if response_error.rewind == Rewind.RESTART:
                self._rewind_conversation_to_first_response()
            elif response_error.rewind == Rewind.ACCUMULATE:
                pass
            elif response_error.rewind == Rewind.REGENERATE:
                self.apply_delete_messages(RangeMessageDesignation.from_(-2, -1))
            elif response_error.rewind == Rewind.AS_FIRST_CORRECTION:
                self._rewind_conversation_to_first_response(offset=2, last=-3)
        else:
            return None

    def run_and_get_valid_result(self):
        self.initialize_conversation_if_needed()
        self._iterate_until_valid_response()
        return self.get_valid_result()

    def get_valid_result(self):
        if isinstance(self.returned_result, NoResponse):
            raise FailedCreatingProductException()
        return self.returned_result
