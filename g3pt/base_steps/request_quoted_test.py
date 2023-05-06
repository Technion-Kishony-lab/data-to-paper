from dataclasses import dataclass


from .base_products_conversers import BaseProductsReviewGPT
from .dual_converser import QuotedReviewDialogDualConverserGPT


@dataclass
class BaseProductsQuotedReviewGPT(QuotedReviewDialogDualConverserGPT, BaseProductsReviewGPT):
    """
    Base class for conversers that specify prior products and then set a goal for the new product
    to be suggested and reviewed.
    The goal is requested from the user as a triple quoted text thereby allowing extraction.
    Option for reviewing the sections (set max_review_turns > 0).
    """
    pass
