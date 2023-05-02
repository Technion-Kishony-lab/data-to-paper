from dataclasses import dataclass

from scientistgpt.gpt_interactors.dual_converser import QuotedReviewDialogDualConverserGPT, ConverserGPT, \
    ReviewDialogDualConverserGPT
from scientistgpt.gpt_interactors.types import Products


@dataclass
class BaseScientificGPT(ConverserGPT):
    products: Products = None
    background_product_fields = None

    def _add_acknowledgement(self, product_field: str, is_last: bool = False):
        thank_you_message = f"Thank you for the {self.products.get_name(product_field)}. \n"
        self.apply_append_surrogate_message(thank_you_message)
        return thank_you_message

    def _add_product_description(self, product_field: str):
        product_description = self.products.get_description(product_field)
        self.apply_append_user_message(product_description)
        return product_description

    def _pre_populate_background(self, previous_product_items: list = None):
        """
        Add background information to the conversation.
        """
        previous_product_items = previous_product_items if previous_product_items is not None \
            else self.background_product_fields
        for i, product_field in enumerate(previous_product_items or []):
            is_last = i == len(previous_product_items) - 1
            self._add_product_description(product_field)
            self._add_acknowledgement(product_field, is_last=is_last)


@dataclass
class BaseScientificReviewGPT(BaseScientificGPT, ReviewDialogDualConverserGPT):
    suppress_printing_other_conversation: bool = False
    max_rounds: int = 1
    termination_phrase: str = "I hereby approve the {goal_noun}"

    def _add_acknowledgement(self, product_field: str, is_last: bool = False):
        thank_you_message = super()._add_acknowledgement(product_field, is_last=is_last)
        if self.are_we_reviewing_at_all:
            thank_you_message += self.user_initiation_prompt if is_last else ''
            self.apply_to_other_append_surrogate_message(thank_you_message)
        return thank_you_message

    def _add_product_description(self, product_field: str):
        product_description = super()._add_product_description(product_field)
        if self.are_we_reviewing_at_all:
            self.apply_to_other_append_user_message(product_description)
        return product_description


@dataclass
class BaseScientificQuotedReviewGPT(BaseScientificReviewGPT, QuotedReviewDialogDualConverserGPT):
    pass
