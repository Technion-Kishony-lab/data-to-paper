from dataclasses import dataclass
from enum import Enum
from typing import Union

from data_to_paper.interactive.app_interactor import AppInteractor


class HumanReviewType(Enum):
    NONE = 'none'  # no human review
    LLM_FIRST = 'llm_first'  # LLM review is sent performed first and sent to human review
    LLM_UPON_REQUEST = 'llm_upon_request'  # LLM review is performed only upon human request

    def __bool__(self):
        return self is not HumanReviewType.NONE


@dataclass
class HumanReviewAppInteractor(AppInteractor):
    human_review: Union[bool, HumanReviewType] = True
    # whether to ask for human review
    # True: HumanReviewType = DEFAULT_HUMAN_REVIEW_TYPE
    # False: HumanReviewType = HumanReviewType.NONE

    @property
    def actual_human_review(self):
        if self.app is None:
            return HumanReviewType.NONE
        if isinstance(self.human_review, bool):
            from data_to_paper.env import DEFAULT_HUMAN_REVIEW_TYPE
            return DEFAULT_HUMAN_REVIEW_TYPE if self.human_review else HumanReviewType.NONE
        return self.human_review
