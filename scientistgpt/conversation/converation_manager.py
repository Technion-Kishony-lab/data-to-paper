from dataclasses import dataclass
from typing import Dict, List, Optional, NamedTuple
import openai

from .conversation import Conversation
from .message import Message, Role
from .actions import Action, AppendMessage, AddComment, DeleteMessages, ResetToTag, RegenerateLastResponse, \
    AddChatgptResponse, FailedChatgptResponse

# Set up the OpenAI API client
from scientistgpt.env import OPENAI_API_KEY, MODEL_ENGINE
openai.api_key = OPENAI_API_KEY


class ConversationNameAndAction(NamedTuple):
    name: str
    action: Action


@dataclass
class ConversationManager:
    """
    Manages multiple conversations with ChatGPT.
    Maintains a complete record of actions performed on these conversations.

    Allows processing Actions that act on the conversation.
    Maintains a list of these actions.
    """

    conversations: Dict[Optional[str]: Conversation]
    """
    a dict containing the managed conversations. The key is typically a string, 
    but can also be `None` for the main/default conversation.
    """

    conversation_names_and_actions: List[ConversationNameAndAction]
    """
    a list of actions, and the conversations to which they were applied, 
    by order in which actions were applied.
    """

    should_print: bool = True
    """
    Indicates whether to print added actions to the console.
    """

    def create_conversation(self, conversation_name: Optional[str] = None):
        self.conversations[conversation_name] = Conversation()

    def get_conversation(self, conversation_name: Optional[str] = None) -> Conversation:
        return self.conversations[conversation_name]

    def _append_and_apply_action(self, action: Action, conversation_name: Optional[str] = None):
        """
        Apply an action to a conversation and append to the actions list.
        """
        self.conversation_names_and_actions.append(ConversationNameAndAction(conversation_name, action))
        action.apply(self.get_conversation(conversation_name))
        if self.should_print:
            action.display(conversation_name)

    def append_message(self, role: Role, content: str, tag: Optional[str],
                       agent: Optional[str] = None,
                       conversation_name: Optional[str] = None,
                       comment: Optional[str] = None):
        """
        Append a message to a specified conversation.
        """
        message = Message(role=role, content=content, tag=tag)
        self._append_and_apply_action(action=AppendMessage(agent=agent, comment=comment, message=message),
                                      conversation_name=conversation_name)

    def append_user_message(self, content: str, tag: Optional[str],
                            agent: Optional[str] = None,
                            conversation_name: Optional[str] = None,
                            comment: Optional[str] = None):
        """
        Append a user-message to a specified conversation.
        """
        self.append_message(role=Role.USER, content=content, tag=tag,
                            agent=agent,
                            conversation_name=conversation_name,
                            comment=comment)

    def append_provided_assistant_message(self, content: str, tag: Optional[str],
                                          agent: Optional[str] = None,
                                          conversation_name: Optional[str] = None,
                                          comment: Optional[str] = None):
        """
        Append a message with a pre-determined assistasnt content to a conversation (as if it came from chatgpt).
        """
        self.append_message(role=Role.ASSISTANT, content=content, tag=tag,
                            agent=agent,
                            conversation_name=conversation_name,
                            comment=comment)

    def get_and_append_assistant_message(self, tag: Optional[str],
                                         agent: Optional[str] = None,
                                         conversation_name: Optional[str] = None,
                                         comment: Optional[str] = None,
                                         removed_messages: List[int] = None):
        """
        Get and append a response from openai to a specified conversation.

        If failed, retry while removing more messages upstream.
        """
        removed_messages = removed_messages or []
        indices_and_messages = self.get_conversation(conversation_name).get_chosen_indices_and_messages(
            removed_messages)
        actual_removed_messages = removed_messages.copy()
        for index, _ in indices_and_messages:
            content = self.try_get_and_append_chatgpt_response(tag=tag, agent=agent,
                                                               conversation_name=conversation_name, comment=comment,
                                                               removed_messages=actual_removed_messages)
            if content is not None:
                return content
            removed_messages.append(index)
        raise RuntimeError('Failed accessing openai despite removing all messages.')

    def get_actions_for_conversation(self, conversation_name: Optional[str] = None) -> List[Action]:
        return [action for name, action in self.conversation_names_and_actions if name == conversation_name]

    def regenerate_previous_response(self, conversation_name: Optional[str] = None):
        last_action = self.get_actions_for_conversation(conversation_name)[-1]
        assert isinstance(last_action, AddChatgptResponse)
        # get response with the same messages removed as last time plus the last response (-1).
        content = self.try_get_chatgpt_response(conversation_name, last_action.removed_messages + [-1])
        assert content is not None  # because this same query already succeeded getting response.
        self._append_and_apply_action(
            action=RegenerateLastResponse(agent=last_action.agent,
                                          comment=last_action.comment,
                                          message=Message(role=last_action.message.role,
                                                          content=content,
                                                          tag=last_action.message.tag),
                                          removed_messages=last_action.removed_messages),
            conversation_name=conversation_name,
        )

    def try_get_chatgpt_response(self,
                                 conversation_name: Optional[str] = None,
                                 removed_messages: List[int] = None) -> Optional[str]:
        """
        Try to get a response from openai to a specified conversation.

        The conversation is sent to openai after removing the messages with indices listed in removed_messages.

        If getting a response is successful then return response string.
        If failed due to openai exception, return None.
        """
        indices_and_messages = self.get_conversation(conversation_name).get_chosen_indices_and_messages(
            removed_messages)
        messages = [message for _, message in indices_and_messages]
        try:
            return self._get_chatgpt_response(messages)
        except openai.error.InvalidRequestError as e:
            return None
        except Exception:
            raise RuntimeError("Failed accessing openai.")

    def try_get_and_append_chatgpt_response(self, tag: Optional[str],
                                             agent: Optional[str] = None,
                                             conversation_name: Optional[str] = None,
                                             comment: Optional[str] = None,
                                             removed_messages: List[int] = None) -> Optional[str]:
        """
        Try to get and append a response from openai to a specified conversation.

        The conversation is sent to openai after removing the messages with indices listed in removed_messages.

        If getting a response is successful then append to the conversation, record action and return response string.
        If failed due to openai exception. Record a failed action and return None.
        """
        content = self.try_get_chatgpt_response(conversation_name=conversation_name, removed_messages=removed_messages)
        if content is None:
            action = FailedChatgptResponse(agent=agent, comment=comment, removed_messages=removed_messages)
        else:
            action = AddChatgptResponse(agent=agent, comment=comment,
                                        removed_messages=removed_messages,
                                        message=Message(role=Role.ASSISTANT,
                                                        content=content,
                                                        tag=tag))
        self._append_and_apply_action(action=action, conversation_name=conversation_name)
        return content

    @staticmethod
    def _get_chatgpt_response(messages: List[Message]) -> str:
        """
        Connect with openai to get response to conversation.
        """
        response = openai.ChatCompletion.create(
            model=MODEL_ENGINE,
            messages=[message.to_chatgpt_dict() for message in messages],
        )
        return response['choices'][0]['message']['content']
