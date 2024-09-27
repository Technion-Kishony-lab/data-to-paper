from dataclasses import dataclass
from enum import Enum
from typing import Optional

from data_to_paper.types import HumanReviewType
from data_to_paper.conversation import ConversationManager, GeneralMessageDesignation, Message
from data_to_paper.text import dedent_triple_quote_str
from data_to_paper.utils.replacer import StrOrReplacer, format_value
from data_to_paper.utils.print_to_file import print_and_log_magenta
from data_to_paper.text.text_counting import is_bulleted_list
from data_to_paper.interactive import PanelNames
from data_to_paper.interactive.human_actions import RequestInfoHumanAction
from data_to_paper.interactive.human_review import HumanReviewAppInteractor
from data_to_paper.env import TEXT_WIDTH, PAUSE_AT_LLM_FEEDBACK, AUTO_TERMINATE_AI_REVIEW
from data_to_paper.run_gpt_code.code_utils import extract_content_of_triple_quote_block, FailedExtractingBlock, \
    IncompleteBlockFailedExtractingBlock
from data_to_paper.servers.model_engine import ModelEngine
from data_to_paper.conversation import Role

from .converser import Converser
from .result_converser import ResultConverser, Rewind


class CycleStatus(Enum):
    FAILED_CHECK_SELF_RESPONSE = 'failed_check_self_response'
    NOT_APPROVED_BY_OTHER = 'not_approved_by_other'
    APPROVED_BY_OTHER = 'approved_by_other'
    MAX_ROUNDS_EXCEEDED = 'max_rounds_exceeded'


@dataclass
class DualConverserGPT(Converser):
    """
    A base class for agents running two LLM agents.
    """
    COPY_ATTRIBUTES = {'other_conversation_name'}

    other_system_prompt: str = 'You are a helpful scientist.'

    other_conversation_name: str = None

    suppress_printing_other_conversation: bool = False

    def __post_init__(self):
        super().__post_init__()
        if self.other_conversation_name is None:
            self.other_conversation_name = f'{self.conversation_name} (other)'

        # For now, we do not allow the other conversation to continue a pre-existing conversation.
        assert self.other_conversation_name not in self.actions_and_conversations.conversations, \
            f'Conversation {self.other_conversation_name} already exists.'

        self.other_conversation_manager = ConversationManager(
            actions_and_conversations=self.actions_and_conversations,
            conversation_name=self.other_conversation_name,
            driver=self.driver if self.driver is not None else type(self).__name__,
            should_print=not self.suppress_printing_other_conversation,
        )

    @property
    def other_conversation(self):
        return self.other_conversation_manager.conversation

    def _pre_populate_other_background(self):
        """
        Add background messages to the other conversation.
        Only called if we are starting a new conversation.
        """
        pass

    def initialize_other_conversation_if_needed(self):
        self.other_conversation_manager.initialize_conversation_if_needed()
        if len(self.other_conversation) == 0:
            self.apply_to_other_append_system_message(self.other_system_prompt)
        self._pre_populate_other_background()

    def apply_to_other_get_and_append_assistant_message(self, tag: Optional[StrOrReplacer] = None,
                                                        comment: Optional[StrOrReplacer] = None,
                                                        is_code: bool = False, previous_code: Optional[str] = None,
                                                        model_engine: Optional[ModelEngine] = None,
                                                        hidden_messages: GeneralMessageDesignation = None,
                                                        expected_tokens_in_response: int = None,
                                                        **kwargs) -> Message:
        model_engine = model_engine or self.model_engine or ModelEngine.DEFAULT
        with self._app_temporarily_set_panel_status(PanelNames.FEEDBACK,
                                                    f'Waiting for Reviewer LLM ({model_engine})...'):
            self._app_send_prompt(PanelNames.FEEDBACK)
            message = self.other_conversation_manager.get_and_append_assistant_message(
                tag=tag,
                comment=comment,
                is_code=is_code, previous_code=previous_code,
                model_engine=model_engine,
                expected_tokens_in_response=expected_tokens_in_response,
                hidden_messages=hidden_messages, **kwargs)
            return message

    def apply_to_other_append_user_message(self, content: StrOrReplacer, tag: Optional[StrOrReplacer] = None,
                                           comment: Optional[StrOrReplacer] = None,
                                           ignore: bool = False,
                                           previous_code: Optional[str] = None, is_background: bool = False,
                                           send_to_app: Optional[bool] = None,
                                           app_panel: PanelNames = PanelNames.FEEDBACK,
                                           editing_title: str = None, editing_instructions: str = None,
                                           in_field_instructions: Optional[str] = None,
                                           sleep_for: Optional[float] = 0,
                                           **kwargs) -> Message:
        if send_to_app is None:
            send_to_app = not is_background and not ignore
        is_edit = editing_title or editing_instructions
        if is_edit:
            content = \
                self._show_and_edit_content(content, editing_title, editing_instructions, in_field_instructions,
                                            send_to_app, app_panel, sleep_for)
        result = self.other_conversation_manager.append_user_message(
            content=format_value(self, content),
            tag=tag,
            comment=comment,
            previous_code=previous_code,
            ignore=ignore, is_background=is_background, **kwargs)
        if not is_edit:
            self._show_and_edit_content(content, editing_title, editing_instructions, in_field_instructions,
                                        send_to_app, app_panel, sleep_for)
        return result

    def apply_to_other_append_system_message(self, content: StrOrReplacer, tag: Optional[StrOrReplacer] = None,
                                             comment: Optional[StrOrReplacer] = None,
                                             **kwargs) -> Message:
        return self.other_conversation_manager.append_system_message(
            content=format_value(self, content),
            tag=tag,
            comment=comment,
            **kwargs)

    def apply_to_other_append_surrogate_message(self, content: StrOrReplacer,
                                                tag: Optional[StrOrReplacer] = None,
                                                comment: Optional[StrOrReplacer] = None,
                                                ignore: bool = False,
                                                previous_code: Optional[str] = None,
                                                is_background: bool = False,
                                                **kwargs) -> Message:
        return self.other_conversation_manager.append_surrogate_message(
            content=format_value(self, content),
            tag=tag,
            comment=comment,
            previous_code=previous_code,
            ignore=ignore, is_background=is_background, **kwargs)

    def apply_to_other_delete_messages(self, message_designation: GeneralMessageDesignation,
                                       comment: Optional[str] = None):
        return self.other_conversation_manager.delete_messages(message_designation, comment=comment)


@dataclass
class DialogDualConverserGPT(DualConverserGPT, ResultConverser, HumanReviewAppInteractor):
    """
    A base class for agents running a dialog between two LLM agents (self and other), where the roles of the two
    agents are reversed. The ASSISTANT response from one conversation is used as the USER response in the other
    conversation, and vice versa.

    A conversation is formed between the two agents. The conversation is terminated when the other agent
    terminates the conversation by issuing a termination_phrase, or when a maximum number of rounds has been reached.

    The conversation can start with self either after its first response or before.
    """

    #                                               end if
    #                         can start             exceeds max_reviewing_rounds
    #                           here                  ^
    #                            |                    |
    #                            v               self_response
    #      end if             SELF.assistant ------------------->  OTHER.user
    # termination_phrase   <---  |                                     |
    # in other_response       SELF.user      <-------------------  OTHER.assistant
    #                           ^                other_response
    #                           |                round_num += 1
    #                         or, can
    #                         start here

    termination_phrase: str = 'Job completed'
    "A phrase used by the 'other' assistant to terminate the conversation."

    respond_to_ambiguous_reviewer_termination: str = None

    # TODO: Responding to ambiguous reviewer leads to the reviewer always apologizing and the conversation is not
    #  sensible anymore.
    #  This can only work if the reviewer is forced to return structured response, like triple-backtick block, or python
    #  list of strings, containing the feedback. or empty of for no feedback.

    # dedent_triple_quote_str("""
    #     Your answer is confusing because you have both provided feedback and included the phrase \t
    #     "{termination_phrase}".
    #     Please correct your response so that you EITHER include constructive feedback, OR just say \t
    #     "{termination_phrase}" without any other text.
    #     Do not apologize for your mistake/confusion - just provide the answer as is.
    #     """)

    append_termination_response_to_self: bool = True

    max_reviewing_rounds: int = 3
    max_reviewer_attempts: int = 4

    rewind_after_end_of_review: Optional[Rewind] = Rewind.AS_FRESH
    # can be
    # DELETE_ALL: delete the entire review including the user initiation prompt.
    # AS_FRESH: keep only the last response posted as fresh
    # ACCUMULATE (default, also None): keep all responses

    def __post_init__(self):
        if not self.are_we_reviewing_at_all:
            # we are not reviewing, so this is essentially a single conversation
            ResultConverser.__post_init__(self)
        else:
            super().__post_init__()
            # reverse roles:
            self.other_conversation_manager.assistant_agent = self.user_agent
            self.other_conversation_manager.user_agent = self.assistant_agent

        self.round_num = 0

    @property
    def are_we_reviewing_at_all(self) -> bool:
        return self.max_reviewing_rounds > 0 or self.actual_human_review

    @property
    def is_last_round(self) -> bool:
        return self.round_num >= self.max_reviewing_rounds

    def get_response_from_self_in_response_to_response_from_other(self, altered_other_response: str) -> Message:
        """
        Append response from other as user message to self conversation, and get response from assistant.
        """
        self.apply_append_user_message(altered_other_response,
                                       sleep_for=0 if self.actual_human_review else PAUSE_AT_LLM_FEEDBACK)
        return self.apply_get_and_append_assistant_message()

    def _alter_self_response(self, response: str) -> str:
        """
        Alter the response from self before sending it to other.
        """
        return response

    def _alter_other_response(self, response: str) -> str:
        """
        Alter the response from other before sending it to self.
        """
        return response

    def get_termination_phrase(self) -> str:
        return format_value(self, self.termination_phrase)

    def _is_reviewer_response_terminating(self, reviewer_response: str, is_human: bool = False) -> Optional[bool]:
        """
        Check if the response from the reviewer indicates that the reviewer is satisfied.
        True: the reviewer is satisfied and the dialog is completed.
        False: the reviewer is not satisfied and the dialog continues.
        None: the reviewer response is ambiguous.
        """
        is_phrase = self.get_termination_phrase().lower() in reviewer_response.lower()
        if is_human:
            return reviewer_response.strip() == '' or is_phrase
        if not is_phrase:
            return False
        if not is_bulleted_list(reviewer_response):
            return True
        return None

    def run_dialog(self) -> CycleStatus:
        """
        Run the dialog until it is completed.
        Returns the reason for termination.
        """
        conversation_len_before_first_round = len(self.conversation)
        while True:
            cycle_status = self.run_one_cycle()
            if cycle_status is not CycleStatus.NOT_APPROVED_BY_OTHER:
                break
        valid_result = self._get_valid_result()
        if self.rewind_after_end_of_review == Rewind.DELETE_ALL:
            self._rewind_conversation_to_first_response(-1, -1, start=conversation_len_before_first_round)
        elif self.rewind_after_end_of_review == Rewind.AS_FRESH:
            self._rewind_conversation_to_first_response(0, -1, start=conversation_len_before_first_round)
            self.apply_append_surrogate_message(self._convert_valid_results_to_fresh_looking_response(valid_result))
        return cycle_status

    def _convert_valid_results_to_fresh_looking_response_and_add_to_other(self) -> str:
        valid_result = self._get_valid_result()
        fresh_looking_self_response = self._convert_valid_results_to_fresh_looking_response(valid_result)
        altered_self_response = self._alter_self_response(fresh_looking_self_response)
        self.apply_to_other_append_user_message(altered_self_response)
        return altered_self_response

    def _get_other_message_and_response(self, auto_terminate: bool = True) -> (Message, str):
        should_terminate = auto_terminate and self.is_last_round
        self.round_num += 1
        if should_terminate:
            return None, self.get_termination_phrase()

        message = self.apply_to_other_get_and_append_assistant_message()
        if self.respond_to_ambiguous_reviewer_termination is not None:
            for attempt in range(self.max_reviewer_attempts):
                is_termination = self._is_reviewer_response_terminating(message.content)
                if is_termination is not None:
                    break
                # The reviewer response is ambiguous
                if attempt > 0:
                    self.apply_to_other_delete_messages(-1)  # delete the last message, to regenerate it
                else:
                    self.apply_to_other_append_user_message(self.respond_to_ambiguous_reviewer_termination)
                message = self.apply_to_other_get_and_append_assistant_message()

        return message, message.content

    def _add_or_replace_other_response(self, response: str):
        is_last_message_user = self.other_conversation[-1].role == Role.USER
        if not is_last_message_user:
            self.apply_to_other_delete_messages(-1)
            assert self.other_conversation[-1].role == Role.USER
        self.apply_to_other_append_surrogate_message(response)

    def _get_human_review(self, llm_review: Optional[str] = None, initial_review: Optional[str] = '') -> Optional[str]:
        goal = format_value(self, self.goal_noun)
        human_review, human_action = self._app_receive_text_and_action(
            PanelNames.FEEDBACK, initial_text=initial_review,
            title='User feedback requested',
            in_field_instructions=f'Give feedback on the {goal} (see Product tab above).\n'
                                  f'Leave blank if you have no suggestions for improvements.',
            optional_suggestions={'AI': llm_review, 'Default': ''})
        if isinstance(human_action, RequestInfoHumanAction):
            assert human_action.value == 'AI'
            return None
        return human_review

    def run_one_cycle(self) -> CycleStatus:
        """
        Run one cycle of the dialog. Makes updates to valid_result by calling
        _check_and_extract_value_from_self_response().
        """
        is_converged, is_new_valid_result = self._iterate_until_valid_response()
        if not is_new_valid_result:
            return CycleStatus.FAILED_CHECK_SELF_RESPONSE

        # We have a valid response from self. Now we can proceed with the dialog:
        if self.is_last_round and not self.actual_human_review:
            return CycleStatus.MAX_ROUNDS_EXCEEDED
        self._convert_valid_results_to_fresh_looking_response_and_add_to_other()

        if self.actual_human_review == HumanReviewType.NONE:
            llm_review_message, llm_review = self._get_other_message_and_response(auto_terminate=True)
            human_review = None
        elif self.actual_human_review == HumanReviewType.LLM_FIRST:
            llm_review_message, llm_review = self._get_other_message_and_response(AUTO_TERMINATE_AI_REVIEW)
            human_review = self._get_human_review(llm_review=llm_review)
        elif self.actual_human_review == HumanReviewType.LLM_UPON_REQUEST:
            llm_review_message, llm_review = None, None
            human_review = self._get_human_review()
            if human_review is None:
                llm_review_message, llm_review = self._get_other_message_and_response(AUTO_TERMINATE_AI_REVIEW)
                if self._is_reviewer_response_terminating(llm_review):
                    llm_review = self.get_termination_phrase()
                human_review = self._get_human_review(llm_review=llm_review, initial_review=llm_review)
        else:
            raise ValueError(f'Unknown HumanReviewType: {self.actual_human_review}')
        review = llm_review if human_review is None else human_review
        self._add_or_replace_other_response(review)
        if self._is_reviewer_response_terminating(review, is_human=human_review is not None):
            if self.append_termination_response_to_self:
                self.apply_append_user_message(
                    review, context=llm_review_message.context if llm_review_message else None,
                    sleep_for=not self.actual_human_review and PAUSE_AT_LLM_FEEDBACK.val)
            return CycleStatus.APPROVED_BY_OTHER

        altered_review = self._alter_other_response(review)
        self.get_response_from_self_in_response_to_response_from_other(altered_review)
        return CycleStatus.NOT_APPROVED_BY_OTHER


@dataclass
class ReviewDialogDualConverserGPT(DialogDualConverserGPT):
    """
    A base class for agents running a dialog between two LLM agents, where one is a "reviwee" who needs to perform
    a task towards a certain "goal", and the other is a "reviewer" who provides constructive feedback.

    The interaction proceeds in repeated cycles of the reviwee performing the task and the reviewer providing feedback.
    """

    # *** Properties that should be set according to the task we want to perform ***

    # roles:
    reviewer: str = 'scientific reviewer'

    other_system_prompt: str = dedent_triple_quote_str("""
        You are a {reviewer} for a {performer} who needs to {goal_verb} {goal_noun}.
        Your job is to advise me, the {performer}, and provide constructive bullet-point feedback in repeated cycles \t
        of improvements and feedback.

        When you feel that the goal has been achieved, respond explicitly with: 
        "{termination_phrase}" (approving-phrase)
        If you feel that the initial {goal_noun} is already good enough, it is perfectly fine and encouraged \t
        to respond with the approving-phrase immediately, without requesting any improvement cycles.
    """)

    sentence_to_add_at_the_end_of_reviewer_response: str = dedent_triple_quote_str("""\n\n
        Please correct your response according to any points you find relevant and applicable in my feedback.
        Send back a complete rewrite of the {goal_noun}.
        Make sure to send the full corrected {goal_noun}, not just the parts that were revised.
        """)

    sentence_to_add_at_the_end_of_performer_response: str = None

    def _alter_other_response(self, response: str) -> str:
        return response + '\n' + self.sentence_to_add_at_the_end_of_reviewer_response

    def _alter_self_response(self, response: str) -> str:
        response = super()._alter_self_response(response)
        if self.sentence_to_add_at_the_end_of_performer_response:
            return response + '\n' + self.sentence_to_add_at_the_end_of_performer_response
        else:
            return response

    def _print_conversation_header(self):
        print_and_log_magenta('==== Starting conversation ' + '=' * (TEXT_WIDTH - 27))
        print_and_log_magenta(self.conversation_name.center(TEXT_WIDTH))
        if self.are_we_reviewing_at_all:
            print_and_log_magenta(self.other_conversation_name.center(TEXT_WIDTH))
        print_and_log_magenta('=' * TEXT_WIDTH)

    def initialize_conversation_if_needed(self):
        super().initialize_conversation_if_needed()
        if self.are_we_reviewing_at_all:
            self.initialize_other_conversation_if_needed()

    def _run_and_return_termination_reason(self, with_review: bool = True) -> CycleStatus:
        if with_review:
            return self.run_dialog()
        else:
            return super()._run_and_return_termination_reason()


@dataclass
class QuotedReviewDialogDualConverserGPT(ReviewDialogDualConverserGPT):
    """
    A base class for agents running a dialog between two LLM agents, where one is a "reviwee" who needs to perform
    a task towards a certain "goal", and the other is a "reviewer" who provides constructive feedback.
    The performer is expected to return the goal as a triple-backtick block, so that it can be extracted.
    """

    your_response_should_be_formatted_as: str = 'a triple-backtick block (but send text, not code).'
    mission_prompt: str = ReviewDialogDualConverserGPT.mission_prompt \
        + '\nYour response should be formatted as {your_response_should_be_formatted_as}'

    sentence_to_add_at_the_end_of_reviewer_response: str = dedent_triple_quote_str("""\n\n
        Please correct your response according to any points you find relevant and applicable in my feedback.
        Send back a complete rewrite of the {goal_noun}.
        Remember, your response should be formatted as {your_response_should_be_formatted_as}
        """)

    rewind_after_getting_a_valid_response: Optional[Rewind] = Rewind.AS_FRESH

    def _convert_extracted_text_to_fresh_looking_response(self, extracted_text: str) -> str:
        return 'Here is the {goal_noun}:\n\n```' + extracted_text + '```\n\n'

    def _check_extracted_text_and_update_valid_result(self, extracted_text: str):
        self._check_flanked_response_is_not_just_header(extracted_text)
        self._update_valid_result(extracted_text)

    def _check_response_and_get_extracted_text(self, response: str) -> str:
        try:
            return extract_content_of_triple_quote_block(response, self.goal_noun, None)
        except FailedExtractingBlock as e:
            self._raise_self_response_error(
                title='# Failed to extract triple quote block',
                error_message=str(e),
                missing_end=isinstance(e, IncompleteBlockFailedExtractingBlock)
            )

    def _check_flanked_response_is_not_just_header(self, response: str):
        if response.count('\n') < 2 and response.count(' ') < 5:
            self._raise_self_response_error(
                title='# Response seems too short',
                error_message='Make sure you are flanking the entire response and not just the headers.'
            )
