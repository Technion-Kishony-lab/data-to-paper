from dataclasses import dataclass
from enum import Enum

from data_to_paper.run_gpt_code.overrides.pvalue import OnStr
from data_to_paper.utils.ref_numeric_values import HypertargetPosition


@dataclass(frozen=True)
class FileContentViewParams:
    """
    Parameters for how to present the content of the file.
    """
    hypertarget_position: HypertargetPosition
    with_hyper_header: bool
    is_block: bool
    pvalue_on_str: OnStr


FINAL_APPENDIX = FileContentViewParams(HypertargetPosition.RAISED_ESCAPE, True, False, OnStr.WITH_ZERO),
FINAL_INLINE = FileContentViewParams(HypertargetPosition.RAISED_ESCAPE, False, False, OnStr.SMALLER_THAN),
PRODUCT = FileContentViewParams(HypertargetPosition.NONE, False, False, OnStr.SMALLER_THAN),
HYPERTARGET_PRODUCT = FileContentViewParams(HypertargetPosition.WRAP, False, False, OnStr.SMALLER_THAN),
CODE_REVIEW = FileContentViewParams(HypertargetPosition.WRAP, False, False, OnStr.SMALLER_THAN),
