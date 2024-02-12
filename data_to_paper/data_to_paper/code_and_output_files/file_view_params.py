from dataclasses import dataclass
from enum import Enum
from typing import Dict, Union, Optional

from data_to_paper.run_gpt_code.overrides.pvalue import OnStr
from data_to_paper.code_and_output_files.ref_numeric_values import HypertargetPosition, HypertargetFormat


class ContentViewPurpose(Enum):
    FINAL_APPENDIX = 0
    FINAL_INLINE = 1
    PRODUCT = 2
    HYPERTARGET_PRODUCT = 3
    CODE_REVIEW = 4


@dataclass(frozen=True)
class ContentViewParams:
    """
    Parameters for how to present the content of the file.
    """
    hypertarget_format: HypertargetFormat
    with_hyper_header: bool
    is_block: bool
    pvalue_on_str: Optional[OnStr]


ContentView = Union[Optional[ContentViewPurpose], ContentViewParams]

DEFAULT_VIEW_PURPOSE_TO_PARAMS: Dict[Optional[ContentViewPurpose], ContentViewParams] = {
    None:
        ContentViewParams(
            hypertarget_format=HypertargetFormat(position=HypertargetPosition.NONE),
            with_hyper_header=False,
            is_block=False,
            pvalue_on_str=None),

    ContentViewPurpose.FINAL_APPENDIX:
        ContentViewParams(
            hypertarget_format=HypertargetFormat(position=HypertargetPosition.ADJACENT, raised=True, escaped=True),
            with_hyper_header=True,
            is_block=False,
            pvalue_on_str=OnStr.WITH_ZERO),

    ContentViewPurpose.FINAL_INLINE:
        ContentViewParams(
            hypertarget_format=HypertargetFormat(position=HypertargetPosition.ADJACENT, raised=True, escaped=False),
            with_hyper_header=False,
            is_block=False,
            pvalue_on_str=OnStr.SMALLER_THAN),

    ContentViewPurpose.PRODUCT:
        ContentViewParams(
            hypertarget_format=HypertargetFormat(position=HypertargetPosition.NONE),
            with_hyper_header=False,
            is_block=False,
            pvalue_on_str=OnStr.SMALLER_THAN),

    ContentViewPurpose.HYPERTARGET_PRODUCT:
        ContentViewParams(
            hypertarget_format=HypertargetFormat(position=HypertargetPosition.WRAP, raised=False, escaped=False),
            with_hyper_header=False,
            is_block=False,
            pvalue_on_str=OnStr.SMALLER_THAN),

    ContentViewPurpose.CODE_REVIEW: ContentViewParams(
        hypertarget_format=HypertargetFormat(position=HypertargetPosition.NONE),
        with_hyper_header=False,
        is_block=True,
        pvalue_on_str=OnStr.SMALLER_THAN),
}
