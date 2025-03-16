from unittest import mock
from dataclasses import dataclass, field

from data_to_paper.base_cast import Agent
from data_to_paper.base_cast.types import Profile
from data_to_paper.base_steps.result_converser import ResultConverser
from data_to_paper.conversation.actions_and_conversations import ActionsAndConversations
from data_to_paper.servers.llm_call import LLM_SERVER_CALLER


class TestAgent(Agent):
    PERFORMER = "performer"
    REVIEWER = "reviewer"

    @classmethod
    def get_primary_agent(cls) -> Agent:
        return cls.PERFORMER

    def get_conversation_name(self) -> str:
        return self.value

    @property
    def profile(self) -> Profile:
        return mock.Mock()


@dataclass
class TestProductsReviewGPT:
    conversation_name: str = "test"
    user_agent: TestAgent = TestAgent.PERFORMER
    assistant_agent: TestAgent = TestAgent.REVIEWER
    actions_and_conversations: ActionsAndConversations = field(
        default_factory=ActionsAndConversations
    )
    max_reviewing_rounds: int = 0


def check_wrong_and_right_responses(
    responses, requester, correct_value, error_texts=(), error_message_number=3
):
    with LLM_SERVER_CALLER.mock(responses, record_more_if_needed=False):
        if hasattr(requester, "run_dialog_and_get_valid_result"):
            assert requester.run_and_get_valid_result() == correct_value
        else:
            assert requester.run_and_get_valid_result() == correct_value

    if not isinstance(error_texts, tuple):
        error_texts = (error_texts,)
    if error_texts:
        error_message = requester.conversation[error_message_number]
        for error_text in error_texts:
            if error_text not in error_message.content:
                print(
                    f"error_text: {error_text}, error_message: {error_message.content}"
                )
                assert False


def replace_apply_get_and_append_assistant_message(converser: ResultConverser):
    """
    Record all calls to apply_get_and_append_assistant_message.
    record in converser.assistant_messages
    """
    converser.called_with_contexts = []
    original_apply_get_and_append_assistant_message = (
        converser.apply_get_and_append_assistant_message
    )

    def apply_get_and_append_assistant_message(*args, **kwargs):
        result = original_apply_get_and_append_assistant_message(*args, **kwargs)
        converser.called_with_contexts.append(converser.conversation[-1].context)
        return result

    converser.apply_get_and_append_assistant_message = (
        apply_get_and_append_assistant_message
    )
