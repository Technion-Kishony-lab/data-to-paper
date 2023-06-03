from unittest import mock
from dataclasses import dataclass, field

from scientistgpt.base_cast import Agent
from scientistgpt.base_cast.types import Profile
from scientistgpt.conversation.actions_and_conversations import ActionsAndConversations
from scientistgpt.servers.chatgpt import OPENAI_SERVER_CALLER


class TestAgent(Agent):
    PERFORMER = 'performer'
    REVIEWER = 'reviewer'

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
    conversation_name: str = 'test'
    user_agent: TestAgent = TestAgent.PERFORMER
    assistant_agent: TestAgent = TestAgent.REVIEWER
    actions_and_conversations: ActionsAndConversations = field(default_factory=ActionsAndConversations)
    max_reviewing_rounds: int = 0


def check_wrong_and_right_responses(responses, requester, correct_value,
                                    error_texts=(), error_message_number=3):
    with OPENAI_SERVER_CALLER.mock(responses, record_more_if_needed=False):
        assert requester.run_dialog_and_get_valid_result() == correct_value

    if not isinstance(error_texts, tuple):
        error_texts = (error_texts,)
    if error_texts:
        error_message = requester.conversation[error_message_number]
        for error_text in error_texts:
            assert error_text in error_message.content
