import copy
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional

from data_to_paper.code_and_output_files.ref_numeric_values import HypertargetPosition, HypertargetFormat
from data_to_paper.run_gpt_code.overrides.pvalue import OnStr


class ViewPurpose(Enum):
    FINAL_APPENDIX = 0
    FINAL_INLINE = 1
    PRODUCT = 2
    HYPERTARGET_PRODUCT = 3
    CODE_REVIEW = 4
    APP_HTML = 5


@dataclass(frozen=True)
class ViewParams:
    """
    Parameters for how to present the content of the file.
    """
    hypertarget_format: HypertargetFormat
    with_hyper_header: bool = False
    is_block: bool = False
    pvalue_on_str: Optional[OnStr] = None


DEFAULT_VIEW_PURPOSE_TO_PARAMS: Dict[ViewPurpose, ViewParams] = {
    None:
        ViewParams(
            hypertarget_format=HypertargetFormat(position=HypertargetPosition.NONE),
            with_hyper_header=False,
            is_block=False,
            pvalue_on_str=None),

    ViewPurpose.FINAL_APPENDIX:
        ViewParams(
            hypertarget_format=HypertargetFormat(position=HypertargetPosition.ADJACENT, raised=True, escaped=True),
            with_hyper_header=True,
            is_block=False,
            pvalue_on_str=OnStr.WITH_ZERO),

    ViewPurpose.FINAL_INLINE:
        ViewParams(
            hypertarget_format=HypertargetFormat(position=HypertargetPosition.ADJACENT, raised=True, escaped=False),
            with_hyper_header=False,
            is_block=False,
            pvalue_on_str=OnStr.SMALLER_THAN),

    ViewPurpose.PRODUCT:
        ViewParams(
            hypertarget_format=HypertargetFormat(position=HypertargetPosition.NONE),
            with_hyper_header=False,
            is_block=True,
            pvalue_on_str=OnStr.SMALLER_THAN),

    ViewPurpose.HYPERTARGET_PRODUCT:
        ViewParams(
            hypertarget_format=HypertargetFormat(position=HypertargetPosition.WRAP, raised=False, escaped=False),
            with_hyper_header=False,
            is_block=True,
            pvalue_on_str=OnStr.SMALLER_THAN),

    ViewPurpose.CODE_REVIEW: ViewParams(
        hypertarget_format=HypertargetFormat(position=HypertargetPosition.NONE),
        with_hyper_header=False,
        is_block=True,
        pvalue_on_str=OnStr.SMALLER_THAN),

    ViewPurpose.APP_HTML: ViewParams(
        hypertarget_format=HypertargetFormat(position=HypertargetPosition.NONE),
        with_hyper_header=False,
        is_block=True,
        pvalue_on_str=OnStr.SMALLER_THAN),
}


class ContentViewPurposeConverter:
    def __init__(self, view_purpose_to_params: Dict[ViewPurpose, ViewParams] = None):
        view_purpose_to_params = view_purpose_to_params or DEFAULT_VIEW_PURPOSE_TO_PARAMS
        self.view_purpose_to_params = copy.deepcopy(view_purpose_to_params)

    def convert_view_purpose_to_view_params(self, view_purpose: ViewPurpose) -> ViewParams:
        return self.view_purpose_to_params[view_purpose]

    def __hash__(self):
        return hash(tuple(self.view_purpose_to_params.items()))

    def __eq__(self, other):
        return isinstance(other, ContentViewPurposeConverter) \
            and self.view_purpose_to_params == other.view_purpose_to_params
