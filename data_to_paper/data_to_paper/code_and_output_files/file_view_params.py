import copy
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
    APP_HTML = 5


@dataclass(frozen=True)
class ContentViewParams:
    """
    Parameters for how to present the content of the file.
    """
    hypertarget_format: HypertargetFormat
    with_hyper_header: bool = False
    is_block: bool = False
    pvalue_on_str: Optional[OnStr] = None
    is_html: bool = False


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
            is_block=True,
            pvalue_on_str=OnStr.SMALLER_THAN),

    ContentViewPurpose.HYPERTARGET_PRODUCT:
        ContentViewParams(
            hypertarget_format=HypertargetFormat(position=HypertargetPosition.WRAP, raised=False, escaped=False),
            with_hyper_header=False,
            is_block=True,
            pvalue_on_str=OnStr.SMALLER_THAN),

    ContentViewPurpose.CODE_REVIEW: ContentViewParams(
        hypertarget_format=HypertargetFormat(position=HypertargetPosition.NONE),
        with_hyper_header=False,
        is_block=True,
        pvalue_on_str=OnStr.SMALLER_THAN),

    ContentViewPurpose.APP_HTML: ContentViewParams(
        hypertarget_format=HypertargetFormat(position=HypertargetPosition.NONE),
        with_hyper_header=False,
        is_block=True,
        pvalue_on_str=OnStr.SMALLER_THAN,
        is_html=True),
}


class ContentViewPurposeConverter:
    def __init__(self, view_purpose_to_params: Dict[Optional[ContentViewPurpose], ContentViewParams] = None):
        view_purpose_to_params = view_purpose_to_params or DEFAULT_VIEW_PURPOSE_TO_PARAMS
        self.view_purpose_to_params = copy.deepcopy(view_purpose_to_params)

    def convert_content_view_to_params(self, content_view: ContentView) -> ContentViewParams:
        if isinstance(content_view, ContentViewPurpose) or content_view is None:
            return self.view_purpose_to_params[content_view]
        elif isinstance(content_view, ContentViewParams):
            return content_view
        else:
            raise ValueError(f'content_view should be either ContentViewPurpose or ContentViewParams, '
                             f'but got {content_view}')

    def __hash__(self):
        return hash(tuple(self.view_purpose_to_params.items()))

    def __eq__(self, other):
        return isinstance(other, ContentViewPurposeConverter) \
            and self.view_purpose_to_params == other.view_purpose_to_params
