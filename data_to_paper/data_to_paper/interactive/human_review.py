from dataclasses import dataclass

from typing import Union

from data_to_paper.interactive.app_interactor import AppInteractor
from data_to_paper.types import HumanReviewType
from data_to_paper.env import DEFAULT_HUMAN_REVIEW_TYPE


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
            return DEFAULT_HUMAN_REVIEW_TYPE if self.human_review else HumanReviewType.NONE
        return self.human_review
