from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, Tuple, Union, Iterable

from data_to_paper.base_steps.converser import Converser
from data_to_paper.base_steps.exceptions import FailedCreatingProductException
from data_to_paper.conversation.message_designation import RangeMessageDesignation, SingleMessageDesignation
from data_to_paper.exceptions import data_to_paperException
from data_to_paper.utils.mutable import Flag
from data_to_paper.utils.print_to_file import print_and_log_red
from data_to_paper.utils.replacer import Replacer, StrOrReplacer, format_value


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
    AS_FRESH: delete (2)-(5) and change (6) to look fresh
    ACCUMULATE: do nothing
    AS_FRESH_CORRECTION: delete (4)-(5)
    DELETE_ALL: delete (1)-(7)
    """

    REGENERATE = 'regenerate'
    # regenerate the last response

    RESTART = 'restart'
    # deleted all iterations and get a fresh response

    AS_FRESH = 'as_fresh'
    # delete all previous responses and modify and post the current response as a fresh response

    ACCUMULATE = 'accumulate'
    # just normally add the current response and the feedback

    AS_FRESH_CORRECTION = 'as_fresh_correction'
    # delete any previous erroneous responses except the first one and modify and post the current response as a fresh
    # response

    DELETE_ALL = 'delete_all'
    # delete all previous responses including the original user initiation prompt


class BumpModel(Enum):
    """
    An enum for the different ways to bump the model upon invalid response.
    """

    DO_NOT_BUMP = 'do_not_bump'

    HIGHER_STRENGTH = 'higher_strength'
    # bump the model to a model with higher strength

    HIGHER_CONTEXT = 'higher_context'
    # bump the model to a model with higher context

    @classmethod
    def from_is_higher_context(cls, is_higher_context: bool):
        return cls.HIGHER_CONTEXT if is_higher_context else cls.HIGHER_STRENGTH

    def __bool__(self):
        return self != self.DO_NOT_BUMP


@dataclass
class SelfResponseError(data_to_paperException):
    """
    Exception raised when the response to a request for a latex section is not acceptable.
    """
    error_message: StrOrReplacer = None
    rewind: Rewind = None
    bump_model: Optional[BumpModel] = None
    add_iterations: int = 0
    # if positive, we will *reduce* the iteration count so that we have more iterations to correct the response

    def __str__(self):
        return self.error_message


class NoResponse:
    pass


ExtractedResult = Union[str, Iterable[str]]


@dataclass
class ResultConverser(Converser):

    performer: str = 'scientist'

    # goal_noun: the desired output of the conversation (expressed as a singular noun).
    goal_noun: str = 'one-paragraph summary on the solar system'

    # goal_verb: a verb applied to achieve the goal, like 'write', 'draw', 'build', 'code', etc.
    goal_verb: str = 'write'

    # *** Properties that are more generic (adjust only if needed) ***

    system_prompt: str = "You are a {performer} who needs to {goal_verb} {goal_noun}."

    mission_prompt: str = "Please {goal_verb} {goal_noun}."

    max_valid_response_iterations: int = 6

    response_to_self_error: str = "{}"
    # {} is the error message. subclasses can add additional text you want to send to self upon error in its response.

    default_rewind_for_result_error: Rewind = Rewind.AS_FRESH
    # Can be any of the Rewind options. In particular:
    # ACCUMULATE: just add and accumulate the response and the error message.
    # AS_FRESH: reformat the response as fresh and repost as if it was the first response.
    # AS_FRESH_CORRECTION: reformat the response as fresh and repost as if it was the second response.
    #                      (the first response is left as is; this is good for responses that include chain-of-thought)

    rewind_after_getting_a_valid_response: Optional[Rewind] = None
    # Can be:
    # DELETE_ALL: leave the conversation as if the exchange never happened
    # AS_FRESH: rewind back to right after the user initiation prompt and post the last response as fresh
    # ACCUMULATE (or `None`): do not do anything. the exchange is left as is.

    _conversation_len_before_first_response: int = None
    _self_response_iteration_count: int = 0
    _is_extracting: Flag = field(default_factory=Flag)

    # Output:
    valid_result: Any = field(default_factory=NoResponse)

    def initialize_conversation_if_needed(self, print_header: bool = True):
        super().initialize_conversation_if_needed(print_header=print_header)
        self._pre_populate_background()
        self._conversation_len_before_first_response = len(self.conversation)

    def _pre_populate_background(self):
        """
        Add background messages to the two conversations to set them ready for the cycle.
        """
        if self.mission_prompt:
            self.apply_append_user_message(self.mission_prompt)

    @property
    def _has_valid_result(self) -> bool:
        """
        Return whether we have a result.
        """
        return not isinstance(self.valid_result, NoResponse)

    def _update_valid_result(self, valid_result: Any):
        """
        Update the valid result. Should be called when we have a result that
        passes all rule-based reviews.
        """
        self.valid_result = valid_result

    def _raise_self_response_error(self,
                                   error_message: StrOrReplacer,
                                   missing_end: bool = False,
                                   rewind: Optional[Rewind] = None,
                                   add_iterations: Optional[int] = None,
                                   bump_model: Optional[BumpModel] = None):
        """
        Raise a SelfResponseError with the given error message and instructions for how to rewind the conversation.

        If we are extracting the result:
        Since we could not extract the result, we cannot repost it as fresh.
        Therefore, the default behavior is:
        - if this is the first response, we add the error message (accumulate).
        - otherwise, we regenerate the response. Because:
          if the first response was extractable, we already have example of a correctly formatted response.
          If the first response was not extractable, we already answered with formatting instructions.
        """
        is_first_response = self._conversation_len_before_first_response == len(self.conversation) - 1
        if self._is_extracting:
            if rewind is None:
                if is_first_response:
                    rewind = Rewind.ACCUMULATE
                else:
                    rewind = Rewind.REGENERATE
            if add_iterations is None:
                add_iterations = 0
            if bump_model is None:
                if missing_end:
                    bump_model = BumpModel.HIGHER_CONTEXT
                else:
                    bump_model = BumpModel.DO_NOT_BUMP
        else:
            if rewind is None:
                rewind = self.default_rewind_for_result_error
            if add_iterations is None:
                add_iterations = 0
            if bump_model is None:
                bump_model = BumpModel.DO_NOT_BUMP
        raise SelfResponseError(format_value(self, error_message), rewind=rewind, bump_model=bump_model,
                                add_iterations=add_iterations)

    def _check_response_and_get_extracted_result(self, response: str) -> ExtractedResult:
        """
        Check the response from self and extract the part(s) that should be used to get the valid result and
        to compose a fresh looking response.
        If there are errors that require self to revise the response, call _raise_self_response_error.
        """
        return response

    def _check_extracted_result_and_get_valid_result(self, extracted_result: ExtractedResult):
        """
        Check the extracted_result and extract the needed information into valid_result.
        If there are errors that require self to revise the response, call _raise_self_response_error.
        """
        self._update_valid_result(extracted_result)

    def _alter_self_response(self, response: str, extracted_results: Optional[ExtractedResult]) -> str:
        """
        Alter the response from self when posted to web.
        This method also used to alter the response to send to other in dual_conversation.
        """
        return self._get_fresh_looking_response(response, extracted_results)

    def _get_fresh_looking_response(self, response: str, extracted_results: Optional[ExtractedResult]) -> str:
        """
        Convert the response to a response that looks as if it was the first response.
        This is called after _check_extracted_result_and_get_valid_result, so the method can in principle
        also use `valid_result`.
        """
        if extracted_results is None:
            return response
        if isinstance(extracted_results, str):
            return extracted_results
        return '\n\n'.join(extracted_results)

    def _rewind_conversation_to_first_response(self, offset: int = 0, last: int = -1, start: int = None):
        """
        Rewind the conversation to the first response + offset.
        offset=0 means that we delete all messages including the first response.
        """
        if start is None:
            start = self._conversation_len_before_first_response
        self.apply_delete_messages(
            RangeMessageDesignation.from_(start + offset, last))

    def _iterate_until_valid_response(self, alter_web_response: bool = False) -> Tuple[Optional[str], Optional[str]]:
        """
        Iterate until we get a valid response from self.
        If we started with a pre-existing self response which was valid, we return it.
        Otherwise, we return the valid message that we got after iterating.
        If we fail to get a valid response after max_valid_response_iterations, return None.
        """
        self._conversation_len_before_first_response = len(self.conversation)
        self_message = None
        self._self_response_iteration_count = 0
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

            if self._self_response_iteration_count == 1 and is_preexisting_self_response:
                self._conversation_len_before_first_response -= 1

            if not is_preexisting_self_response:
                self_message = self.apply_get_and_append_assistant_message(web_conversation_name=None)
                self_response = self_message.content

            # check if the response is valid:
            response_error = None
            extracted_results = None
            try:
                with self._is_extracting.temporary_set(True):
                    extracted_results = self._check_response_and_get_extracted_result(self_response)
            except SelfResponseError as e:
                response_error = e
            if not response_error:
                try:
                    self._check_extracted_result_and_get_valid_result(extracted_results)
                except SelfResponseError as e:
                    response_error = e

            if not is_preexisting_self_response:
                self.apply_append_surrogate_message(
                    content=(self_response if response_error or not alter_web_response
                             else self._alter_self_response(self_response, extracted_results)),
                    conversation_name=None, context=self_message.context)

            if response_error:
                self._self_response_iteration_count -= response_error.add_iterations
                if response_error.bump_model:
                    try:
                        if response_error.bump_model == BumpModel.HIGHER_STRENGTH:
                            self.model_engine = self.model_engine.get_model_with_more_strength()
                        elif response_error.bump_model == BumpModel.HIGHER_CONTEXT:
                            self.model_engine = self.model_engine.get_model_with_more_context()
                        model_was_bumped = True
                    except ValueError:
                        model_was_bumped = False
                    if model_was_bumped:
                        msg = f"You seem totally drunk. Let's Bump you to {self.model_engine} and try again..."
                        self.apply_append_user_message(msg, conversation_name=None)  # web only
                        print_and_log_red(msg)

            rewind = response_error.rewind if response_error else self.rewind_after_getting_a_valid_response

            # replace the response with a fresh looking response if needed:
            cycle_num = (len(self.conversation) - self._conversation_len_before_first_response + 1) // 2
            if rewind == Rewind.AS_FRESH or rewind == Rewind.AS_FRESH_CORRECTION and cycle_num > 1:
                self.apply_delete_messages(SingleMessageDesignation(-1))
                self.apply_append_surrogate_message(self._get_fresh_looking_response(self_response, extracted_results),
                                                    web_conversation_name=None)
            # add the error message:
            if response_error:
                self.apply_append_user_message(
                    Replacer(self, self.response_to_self_error, args=(response_error.error_message,)))

            # rewind:
            if rewind == Rewind.RESTART:
                self._rewind_conversation_to_first_response()
            elif rewind == Rewind.ACCUMULATE or rewind is None:
                pass
            elif rewind == Rewind.REGENERATE:
                assert response_error
                self.apply_delete_messages(RangeMessageDesignation.from_(-2, -1))
            elif rewind == Rewind.AS_FRESH_CORRECTION:
                assert response_error
                self._rewind_conversation_to_first_response(offset=2, last=-3)
            elif rewind == Rewind.DELETE_ALL:
                self._rewind_conversation_to_first_response(-1)  # delete including the user initiation prompt
            elif rewind == Rewind.AS_FRESH:
                self._rewind_conversation_to_first_response(offset=0, last=-3 if response_error else -2)

            if not response_error:
                return self_response, extracted_results
        else:
            if not self._has_valid_result:
                raise FailedCreatingProductException()
        return None, None

    def run_and_get_valid_result(self):
        self.initialize_conversation_if_needed()
        self._iterate_until_valid_response()
        return self.get_valid_result()

    def get_valid_result(self):
        if not self._has_valid_result:
            raise FailedCreatingProductException()
        return self.valid_result
