from dataclasses import dataclass


from .base_products_conversers import ReviewBackgroundProductsConverser
from .dual_converser import QuotedReviewDialogDualConverserGPT


@dataclass
class BaseProductsQuotedReviewGPT(QuotedReviewDialogDualConverserGPT, ReviewBackgroundProductsConverser):
    """
    Base class for conversers that specify prior products and then set a goal for the new product
    to be suggested and reviewed.
    The goal is requested from the user as a triple-backtick text thereby allowing extraction.
    Option for reviewing the sections (set max_review_turns > 0).
    """

    def __post_init__(self):
        ReviewBackgroundProductsConverser.__post_init__(self)
        QuotedReviewDialogDualConverserGPT.__post_init__(self)
