import litellm
import openai
from pytest import fixture

from data_to_paper import Role, Message
from data_to_paper.servers.llm_call import LLM_MAX_CONTENT_LENGTH_MESSAGE_CONTAINS
from data_to_paper.servers.model_engine import ModelEngine
from data_to_paper.servers.model_manager import ModelManager


@fixture()
def conversation(conversations):
    conversation = conversations.get_or_create_conversation(conversation_name="default")
    conversation.append(Message(Role.SYSTEM, "You are a helpful assistant."))
    conversation.append(Message(Role.USER, "Write a short code.", "write_code"))
    conversation.append(
        Message(
            Role.ASSISTANT, "Here is my code:\n\n```python\nprint(7)\n```\n", "code"
        )
    )
    conversation.append(Message(Role.USER, "How are you?"))
    return conversation


@fixture()
def openai_exception():
    current_model = ModelEngine(ModelManager.get_instance().get_current_model())

    return litellm.InvalidRequestError(
        message=LLM_MAX_CONTENT_LENGTH_MESSAGE_CONTAINS,
        model=current_model.value,
        llm_provider=current_model.server_name,
    )
