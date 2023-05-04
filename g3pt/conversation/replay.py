from __future__ import annotations
from pathlib import Path

from typing import Union

from .actions import apply_action
from .actions_and_conversations import clear_actions_and_conversations, load_actions_from_file


def replay_actions(file_path: Union[str, Path], should_print: bool = True, is_color: bool = True):
    """
    Replay a list of actions on conversations.
    """
    clear_actions_and_conversations()

    new_actions = load_actions_from_file(file_path)
    for action in new_actions:
        apply_action(action, should_print=should_print, is_color=is_color)

    return new_actions
