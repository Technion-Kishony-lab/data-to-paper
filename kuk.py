from dataclasses import dataclass
from typing import Union, Optional, NamedTuple

NoneType = type(None)


class Action(NamedTuple):
    """
    Base class for actions performed on a chatgpt conversation.
    """

    "The agent/algorithm performing the action."
    agent: Optional[str] = None

    "A comment explaining why action is performed."
    comment: Optional[str] = None

    def display(self):
        if self.agent:
            print(f'{self.agent}: ', end='')
        print(f'<{type(self).__name__}> {self.comment}')


class AddMessage(Action):
    """
    Append a message to the conversation.

    Message will be tagged with `tag`.
    If `tag` already exists, conversation will reset to the previous tag.
    """
    role: str
    content: str = ''
    tag: Optional[str] = None

    def display(self):
        super().display()
        print([*self])


am = AddMessage(agent='ag')
am.display()

