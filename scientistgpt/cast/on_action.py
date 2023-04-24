from __future__ import annotations

from typing import TYPE_CHECKING

from .cast import set_system_prompt

if TYPE_CHECKING:
    from scientistgpt.conversation.actions import Action


def update_messengers_on_action(action: Action):
    """
    This is called after an action was applied to a conversation.
    """
    from .messenger import ALL_MESSENGERS

    # update the Agent system_prompt if needed:
    from scientistgpt import Role
    from scientistgpt.conversation.actions import AppendMessage
    if isinstance(action, AppendMessage) and action.message.role is Role.SYSTEM:
        set_system_prompt(agent=action.message.agent, prompt=action.message.content)

    # update the Messenger system:
    for messenger in ALL_MESSENGERS:
        if messenger.first_person in action.conversation.participants:
            messenger.on_action(action)
