from dataclasses import dataclass


@dataclass(frozen=True)
class HumanInteractions:
    edit_other_response: bool = True
    edit_self_response: bool = False  # False: never; True: always; None: only after passing rule-based checks
    edit_code_review: bool = True
