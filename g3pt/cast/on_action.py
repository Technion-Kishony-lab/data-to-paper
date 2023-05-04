from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from g3pt.conversation.actions import Action


def update_cast_on_action(action: Action):
    """
    This is called after an action was applied to a conversation.
    """
    from . import cast
    from . import messenger

    # Update the Agents:
    cast.on_action(action)

    # Update the Messengers:
    messenger.on_action(action)
