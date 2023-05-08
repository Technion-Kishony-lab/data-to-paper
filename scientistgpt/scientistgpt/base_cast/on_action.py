from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from scientistgpt.conversation import Action


def update_cast_and_messenger_on_action(action: Action):
    """
    This is called after an action was applied to a conversation.
    """
    from . import cast
    from . import messenger

    # Update the Agents:
    cast.on_action(action)

    # Update the Messengers:
    messenger.on_action(action)
