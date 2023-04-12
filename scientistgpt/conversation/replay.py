from __future__ import annotations
import pickle
from pathlib import Path

from typing import List, Union

from .actions import Action
from .actions_and_conversations import CONVERSATION_NAMES_TO_CONVERSATIONS, APPLIED_ACTIONS


def save_actions_to_file(file_path: Union[str, Path]):
    """
    Save the primary list of actions to a json file.
    """
    with open(file_path, 'wb') as f:
        pickle.dump(APPLIED_ACTIONS, f)


def load_actions_from_file(file_path: str) -> List[Action]:
    """
    Load a list of actions from a json file.
    """
    with open(file_path, 'rb') as f:
        return pickle.load(f)


def clear_actions_and_conversations():
    """
    Clear the primary list of actions.
    """
    APPLIED_ACTIONS.clear()
    CONVERSATION_NAMES_TO_CONVERSATIONS.clear()


def replay_actions(file_path: str):
    """
    Replay a list of actions on conversations.
    """
    clear_actions_and_conversations()

    new_actions = load_actions_from_file(file_path)
    for action in new_actions:
        action.apply()
        APPLIED_ACTIONS.append(action)
