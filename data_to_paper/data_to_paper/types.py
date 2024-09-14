from enum import Enum


class HumanReviewType(Enum):
    NONE = 'none'  # no human review
    LLM_FIRST = 'llm_first'  # LLM review is performed first and sent to human review
    LLM_UPON_REQUEST = 'llm_upon_request'  # LLM review is performed only upon human request

    def __bool__(self):
        return self is not HumanReviewType.NONE
