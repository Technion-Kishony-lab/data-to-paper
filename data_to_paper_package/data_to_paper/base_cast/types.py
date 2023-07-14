from enum import Enum
from typing import NamedTuple, Optional


class Algorithm(Enum):
    GPT = 'GPT'
    PRE_PROGRAMMED = 'PRE_PROGRAMMED'
    MIXED = 'MIXED'

    def pretty_repr(self, prompt: Optional[str] = None) -> str:
        if prompt is None:
            prompt_statement = f"I am still waiting to be given a mission statement (please check in later)."
        else:
            prompt_statement = f"I have been given the following mission statement:\n{prompt}\n"

        if self == Algorithm.GPT:
            return f"I am run by GPT.\n{prompt_statement}"
        elif self == Algorithm.PRE_PROGRAMMED:
            return f"I am run by a pre-programmed algorithm issuing automated programmed responses."
        elif self == Algorithm.MIXED:
            return f"I am run by combination of a pre-programmed algorithm issuing automated programmed responses,\n" \
                   f"and by GPT.\n{prompt_statement}"
        else:
            raise ValueError(f"Unknown algorithm: {self}")


class Profile(NamedTuple):
    agent_name: str
    name: str
    title: str
    description: str
    image_file: str
    algorithm: Algorithm
