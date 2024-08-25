import copy
from enum import Enum
from typing import Dict

from data_to_paper.code_and_output_files.ref_numeric_values import HypertargetPosition, HypertargetFormat


class ViewPurpose(Enum):
    FINAL_APPENDIX = 0
    FINAL_INLINE = 1
    PRODUCT = 2
    HYPERTARGET_PRODUCT = 3
    CODE_REVIEW = 4
    APP_HTML = 5

    def is_for_llm(self):
        return self in [ViewPurpose.PRODUCT, ViewPurpose.HYPERTARGET_PRODUCT, ViewPurpose.CODE_REVIEW]

    def is_for_paper(self):
        return self in [ViewPurpose.FINAL_APPENDIX, ViewPurpose.FINAL_INLINE]

    def is_for_html(self):
        return self in [ViewPurpose.APP_HTML]


DEFAULT_VIEW_PURPOSE_TO_HYPERTARGET_FORMAT: Dict[ViewPurpose, HypertargetFormat] = {
    None: HypertargetFormat(position=HypertargetPosition.NONE),
    ViewPurpose.FINAL_APPENDIX: HypertargetFormat(position=HypertargetPosition.ADJACENT, raised=True, escaped=True),
    ViewPurpose.FINAL_INLINE: HypertargetFormat(position=HypertargetPosition.ADJACENT, raised=True, escaped=False),
    ViewPurpose.PRODUCT: HypertargetFormat(position=HypertargetPosition.NONE),
    ViewPurpose.HYPERTARGET_PRODUCT: HypertargetFormat(position=HypertargetPosition.WRAP, raised=False, escaped=False),
    ViewPurpose.CODE_REVIEW: HypertargetFormat(position=HypertargetPosition.NONE),
    ViewPurpose.APP_HTML: HypertargetFormat(position=HypertargetPosition.NONE),
}


class ContentViewPurposeConverter:
    def __init__(self, view_purpose_to_params: Dict[ViewPurpose, HypertargetFormat] = None):
        view_purpose_to_params = view_purpose_to_params or DEFAULT_VIEW_PURPOSE_TO_HYPERTARGET_FORMAT
        self.view_purpose_to_params = copy.deepcopy(view_purpose_to_params)

    def convert_view_purpose_to_hypertarget_format(self, view_purpose: ViewPurpose) -> HypertargetFormat:
        return self.view_purpose_to_params[view_purpose]

    def __hash__(self):
        return hash(tuple(self.view_purpose_to_params.items()))

    def __eq__(self, other):
        return isinstance(other, ContentViewPurposeConverter) \
            and self.view_purpose_to_params == other.view_purpose_to_params
