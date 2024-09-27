from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, Tuple, Union, Iterable, Type

from data_to_paper.base_products.product import Product, ValueProduct
from data_to_paper.base_steps.converser import Converser
from data_to_paper.base_steps.exceptions import FailedCreatingProductException
from data_to_paper.conversation.message_designation import RangeMessageDesignation, SingleMessageDesignation
from data_to_paper.conversation.stage import Stage
from data_to_paper.env import PAUSE_AT_RULE_BASED_FEEDBACK
from data_to_paper.exceptions import data_to_paperException
from data_to_paper.interactive import PanelNames
from data_to_paper.text.highlighted_text import format_text_with_code_blocks
from data_to_paper.utils.mutable import Flag
from data_to_paper.utils.print_to_file import print_and_log_red
from data_to_paper.utils.replacer import StrOrReplacer, format_value


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
    error_message: str = None
    title: str = ''
    formatting_instructions: str = None
    rewind: Rewind = None
    bump_model: Optional[BumpModel] = None
    add_iterations: int = 0
    # if positive, we will *reduce* the iteration count so that we have more iterations to correct the response

    def __str__(self):
        return f'SelfResponseError: {self.error_message}'


class NoResponse:
    pass


ExtractedText = Union[str, Iterable[str]]


@dataclass
class ResultConverser(Converser):
    """
    A converser that is designed to extract a result from a conversation.
    response        ---> extracted_text ---> valid_result --> Product
                                                                /
    fresh_response  <--- extracted_text <--- valid_result  <---
    """

    performer: str = 'scientist'

    # goal_noun: the desired output of the conversation (expressed as a singular noun).
    goal_noun: str = 'one-paragraph summary on the solar system'

    # goal_verb: a verb applied to achieve the goal, like 'write', 'draw', 'build', 'code', etc.
    goal_verb: str = 'write'

    # *** Properties that are more generic (adjust only if needed) ***

    system_prompt: str = "You are a {performer} who needs to {goal_verb} {goal_noun}."

    mission_prompt: str = "Please {goal_verb} {goal_noun}."

    max_valid_response_iterations: int = 6

    your_response_should_be_formatted_as: str = ""

    formatting_instructions_for_feedback: str = \
        "Remember, your response should be formatted as {your_response_should_be_formatted_as}"

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
    stage: Stage = None
    product_type: Type[ValueProduct] = None  # the type of the product to be generated. If None, non-product result.
    valid_result: Union[Product, Any] = field(default_factory=NoResponse)
    _valid_result_update_count: int = 0

    def get_valid_result_as_html(self) -> str:
        valid_result = self._get_valid_result()
        if isinstance(valid_result, Product):
            return valid_result.as_html(2)
        return format_text_with_code_blocks(self.get_valid_result_as_markdown(), width=None, is_html=True, from_md=True)

    def get_valid_result_as_markdown(self) -> str:
        valid_result = self._get_valid_result()
        if isinstance(valid_result, Product):
            return valid_result.as_formatted_text(2)
        return str(valid_result)

    def _upon_conversation_initiation(self):
        super()._upon_conversation_initiation()
        if self.goal_noun:
            self._app_set_header(self.conversation_name)

    def initialize_conversation_if_needed(self):
        super().initialize_conversation_if_needed()
        self._pre_populate_background()
        self._conversation_len_before_first_response = len(self.conversation)

    def _pre_populate_background(self):
        """
        Add background messages to the two conversations to set them ready for the cycle.
        """
        if self.mission_prompt:
            self.apply_append_user_message(self.mission_prompt, app_panel=PanelNames.MISSION_PROMPT,
                                           editing_title='Revise as needed',
                                           in_field_instructions='Write the mission prompt.')

    @property
    def _has_valid_result(self) -> bool:
        """
        Return whether we have a result.
        """
        return not isinstance(self.valid_result, NoResponse)

    def _update_valid_result(self, valid_result: Union[Product, Any]):
        """
        Update the valid result.
        Should be called when we have a result that is "usable".
        Typically, the method is called after passing all rule-based checks.
        But can also be called when we have a result that passed key rules but not others so is "good enough"
        to be declared as "valid". It will be used in case the improvement iteration count is reached.
        """
        valid_result = self._convert_valid_result_to_product(valid_result)
        if isinstance(valid_result, Product):
            if valid_result.stage is None:
                valid_result.stage = self.stage
        self.valid_result = valid_result
        self._valid_result_update_count += 1
        if self.app:
            if self._has_valid_result:
                html = self.get_valid_result_as_html()
            else:
                html = "No result yet."
            self._app_send_prompt(PanelNames.PRODUCT, html, provided_as_html=True)

    def _raise_self_response_error(self,
                                   title: str,
                                   error_message: StrOrReplacer,
                                   formatting_instructions: StrOrReplacer = None,
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
        raise SelfResponseError(format_value(self, error_message),
                                title=title, formatting_instructions=formatting_instructions,
                                rewind=rewind, bump_model=bump_model,
                                add_iterations=add_iterations)

    def _convert_response_error_to_error_message(self, response_error: SelfResponseError) -> str:
        """
        Convert the response error to an error message.
        """
        formatting_instructions = response_error.formatting_instructions or self.formatting_instructions_for_feedback
        return format_value(self, response_error.title) + '\n' + format_value(self, response_error.error_message) \
            + '\n' + format_value(self, formatting_instructions)

    """
    Response --> extracted_text --> valid_result --> Product
    """

    def _check_response_and_get_extracted_text(self, response: str) -> ExtractedText:
        """
        # Response --> extracted_text #
        Check the response from self and extract the part(s) that should be used to get the valid result and
        to compose a fresh looking response.
        If there are errors that require self to revise the response, call _raise_self_response_error.
        """
        return response

    def _check_extracted_text_and_update_valid_result(self, extracted_text: ExtractedText):
        """
        # extracted_text --> valid_result #
        Check the extracted_text and extract the needed information into valid_result.
        If we get a result that is "usable", we update it using valid_result, by calling _update_valid_result.
        If there are errors that require self to revise the response, call _raise_self_response_error.
        Normally, we should either _update_valid_result or _raise_self_response_error, but we can do both if we have a
        result that is "good enough" to be declared as "valid", but we are still trying to improve it with further
        rule-based feedback.
        """
        self._update_valid_result(extracted_text)

    def _convert_valid_result_to_product(self, valid_result: Any) -> Union[Product, Any]:
        """
        # valid_result --> Product #
        Convert the valid result to a product.
        """
        if self.product_type is None:
            return valid_result
        return self.product_type(value=valid_result)

    """
    fresh_response <-- extracted_text <-- valid_result <-- Product
    """

    def _convert_extracted_text_to_fresh_looking_response(self, extracted_text: ExtractedText) -> str:
        """
        # fresh_response <-- extracted_text #
        Convert the extracted text to a response that can be posted to the conversation.
        """
        if isinstance(extracted_text, str):
            return extracted_text
        return '\n\n'.join(extracted_text)

    def _convert_valid_result_back_to_extracted_text(self, valid_result: Any) -> ExtractedText:
        """
        # extracted_text <-- valid_result #
        Convert the valid result to an extracted result.
        """
        return str(valid_result)

    def _convert_product_back_to_valid_result(self, product: Union[Product, Any]) -> Any:
        """
        # valid_result <-- Product #
        Convert the product to a valid result.
        """
        if isinstance(product, ValueProduct):
            return product.value
        return product

    def _convert_valid_results_to_fresh_looking_response(self, valid_results: Any) -> str:
        """
        # fresh_response <-- extracted_text <-- valid_result <-- Product #
        Convert the valid results to a response that can be posted to the conversation.
        """
        valid_results = self._convert_product_back_to_valid_result(valid_results)
        extracted_text = self._convert_valid_result_back_to_extracted_text(valid_results)
        fresh_response = self._convert_extracted_text_to_fresh_looking_response(extracted_text)
        return fresh_response

    def _rewind_conversation_to_first_response(self, offset: int = 0, last: int = -1, start: int = None):
        """
        Rewind the conversation to the first response + offset.
        offset=0 means that we delete all messages including the first response.
        """
        if start is None:
            start = self._conversation_len_before_first_response
        self.apply_delete_messages(
            RangeMessageDesignation.from_(start + offset, last))

    def _iterate_until_valid_response(self) -> Tuple[bool, bool]:
        """
        Iterate until we get a valid response from self (return is_converged=True),
        or until we exceed max_valid_response_iterations (return is_converged=False).
        Note that even if we did not get a fully valid response,
        we may still have a "usable" result in self.valid_result (is_new_valid_result=True).
        return (converged, is_new_valid_result)
        """
        self._conversation_len_before_first_response = len(self.conversation)
        self_message = None
        self_response = None
        self._self_response_iteration_count = 0
        initial_valid_result_update_count = self._valid_result_update_count
        is_new_valid_result = False
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
                self_message = self.apply_get_and_append_assistant_message()
                self_response = self_message.content

            # check if the response is valid:
            with self._app_temporarily_set_panel_status(PanelNames.FEEDBACK, 'Rule-based check ...'):
                self._app_send_prompt(PanelNames.FEEDBACK)
                response_error = None
                extracted_text = None
                try:
                    with self._is_extracting.temporary_set(True):
                        extracted_text = self._check_response_and_get_extracted_text(self_response)
                except SelfResponseError as e:
                    response_error = e
                if not response_error:
                    try:
                        self._check_extracted_text_and_update_valid_result(extracted_text)
                    except SelfResponseError as e:
                        response_error = e
                is_new_valid_result = self._valid_result_update_count > initial_valid_result_update_count

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
                        print_and_log_red(msg)
            # else:
            #     self._app_send_prompt(PanelNames.FEEDBACK,
            #                           f'## {Symbols.CHECK_SYMBOL} Rule-based check passed.\n'
            #                           'The LLM response has successfully passed all rule-based checks.',
            #                           from_md=True,
            #                           sleep_for=PAUSE_AT_RULE_BASED_FEEDBACK)

            rewind = response_error.rewind if response_error else self.rewind_after_getting_a_valid_response

            # replace the response with a fresh looking response if needed:
            cycle_num = (len(self.conversation) - self._conversation_len_before_first_response + 1) // 2
            if (rewind == Rewind.AS_FRESH or rewind == Rewind.AS_FRESH_CORRECTION and cycle_num > 1) \
                    and extracted_text:
                self.apply_delete_messages(SingleMessageDesignation(-1))
                self.apply_append_surrogate_message(
                    self._convert_extracted_text_to_fresh_looking_response(extracted_text))
            # add the rule-based error message:
            if response_error:
                self.apply_append_user_message(self._convert_response_error_to_error_message(response_error),
                                               sleep_for=PAUSE_AT_RULE_BASED_FEEDBACK)

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
                assert is_new_valid_result
                return True, is_new_valid_result
        else:
            return False, is_new_valid_result

    def _get_valid_result(self) -> Union[Product, Any]:
        if not self._has_valid_result:
            raise FailedCreatingProductException('Failed to create a valid result.')
        return self.valid_result

    def _post_run(self):
        """
        Post-run actions.
        """
        pass

    def _run_and_return_termination_reason(self, *args, **kwargs) -> Any:
        """
        Run the conversation.
        """
        return self._iterate_until_valid_response()

    def run_and_get_valid_result_and_termination_reason(self, *args, **kwargs) -> Tuple[Tuple[bool, bool], Any]:
        """
        Run the conversation until we get a valid result.
        Return whether the conversation is converged and whether we have a new valid result.
        """
        self.initialize_conversation_if_needed()
        termination_reason = self._run_and_return_termination_reason(*args, **kwargs)
        result = self._get_valid_result()  # raises FailedCreatingProductException if no valid result
        self._post_run()
        return result, termination_reason

    def run_and_get_valid_result(self, *args, **kwargs) -> Any:
        """
        Run the conversation until we get a valid result.
        Return the valid result.
        """
        if not self._has_valid_result:
            self.run_and_get_valid_result_and_termination_reason(*args, **kwargs)
        return self._get_valid_result()
