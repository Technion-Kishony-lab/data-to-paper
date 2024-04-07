from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class HumanInteractions:
    edit_other_response: bool = True
    edit_self_response: bool = False  # False: never; True: always; None: only after passing rule-based checks
    edit_code_review: bool = True


class PanelNames(Enum):
    SYSTEM_PROMPT = "System Prompt"
    MISSION_PROMPT = "Mission Prompt"
    PRODUCT = "Product"
    RESPONSE = "Response"
    FEEDBACK = "Feedback"
