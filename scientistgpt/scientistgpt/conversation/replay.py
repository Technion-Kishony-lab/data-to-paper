from __future__ import annotations
from pathlib import Path

from typing import Union

from .actions_and_conversations import Actions


def replay_actions(file_path: Union[str, Path], is_color: bool = True):
    """
    Replay a list of actions on conversations.
    """
    actions = Actions()

    actions.load_actions_from_file(file_path)
    for action in actions:
        actions.apply_action(action, is_color=is_color, should_append=False)

    return actions
