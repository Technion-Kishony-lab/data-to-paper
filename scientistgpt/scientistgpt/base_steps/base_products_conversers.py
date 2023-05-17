from dataclasses import dataclass
from pathlib import Path
from typing import List

from .types import Products
from .dual_converser import ConverserGPT, ReviewDialogDualConverserGPT
from ..utils.copier import Copier
from ..utils.text_utils import NiceList


@dataclass
class BaseProductsHandler(Copier):
    """
    Base class for steps that deal with Products and may also create output files.
    """
    COPY_ATTRIBUTES = {'products', 'output_directory'}

    products: Products = None

    output_directory: Path = None  # if not None, save any output files to this directory

    def __post_init__(self):
        if self.output_directory:
            self.output_directory = Path(self.output_directory).absolute()

    def _move_files_to_output_directory(self, file_paths: List[Path]):
        """
        Move any output files to the output directory.
        """
        if self.output_directory:
            for file_path in file_paths:
                file_path.rename(self.output_directory / file_path.name)


@dataclass
class BaseProductsGPT(BaseProductsHandler, ConverserGPT):
    COPY_ATTRIBUTES = BaseProductsHandler.COPY_ATTRIBUTES | ConverserGPT.COPY_ATTRIBUTES

    def __post_init__(self):
        BaseProductsHandler.__post_init__(self)
        ConverserGPT.__post_init__(self)


@dataclass
class BaseBackgroundProductsGPT(BaseProductsGPT):
    """
    Base class for conversers that deal with Products.
    Allows for the addition of background information about prior products to the conversation.
    """
    ADDITIONAL_DICT_ATTRS = BaseProductsGPT.ADDITIONAL_DICT_ATTRS | {'background_product_names'} | {'actual_background_product_fields'}

    background_product_fields = []
    product_acknowledgement: str = "Thank you for the {{}}. \n"

    fake_performer_request_for_help: str = None
    fake_reviewer_agree_to_help: str = "Sure, just please provide some background first.\n"

    @property
    def background_product_names(self) -> NiceList[str]:
        return NiceList((self.products.get_name(product_field) for product_field in self.background_product_fields),
                        wrap_with='"', separator=', ', last_separator=' and ')

    @property
    def actual_background_product_fields(self):
        return self.background_product_fields

    def _add_acknowledgement(self, product_field: str, is_last: bool = False):
        thank_you_message = self.product_acknowledgement.format(self.products.get_name(product_field))
        self.apply_append_surrogate_message(
            content=thank_you_message, tag=f'background_thanks_{product_field}', is_background=True,
            reverse_roles_for_web=True)
        return thank_you_message

    def _add_product_description(self, product_field: str):
        product_description = self.products.get_description(product_field)
        self.apply_append_user_message(
            content=product_description, tag=f'background_{product_field}', is_background=True,
            reverse_roles_for_web=True)
        return product_description

    def _add_fake_pre_conversation_exchange(self):
        """
        Add fake exchange to the conversation before providing background information.
        """
        if self.fake_performer_request_for_help:
            self.apply_append_surrogate_message(
                content=self.fake_performer_request_for_help, ignore=True)
            if self.fake_reviewer_agree_to_help:
                self.apply_append_user_message(
                    content=self.fake_reviewer_agree_to_help, ignore=True)

    def _pre_populate_background(self):
        """
        Add background information to the conversation.
        """
        self._add_fake_pre_conversation_exchange()
        previous_product_items = self.actual_background_product_fields
        for i, product_field in enumerate(previous_product_items or []):
            is_last = i == len(previous_product_items) - 1
            self._add_product_description(product_field)
            self._add_acknowledgement(product_field, is_last=is_last)


@dataclass
class BaseProductsReviewGPT(BaseBackgroundProductsGPT, ReviewDialogDualConverserGPT):
    """
    Base class for conversers that specify prior products and then set a goal for the new product
    to be suggested and reviewed.
    """
    COPY_ATTRIBUTES = BaseBackgroundProductsGPT.COPY_ATTRIBUTES | ReviewDialogDualConverserGPT.COPY_ATTRIBUTES
    ADDITIONAL_DICT_ATTRS = \
        BaseBackgroundProductsGPT.ADDITIONAL_DICT_ATTRS | ReviewDialogDualConverserGPT.ADDITIONAL_DICT_ATTRS
    suppress_printing_other_conversation: bool = False
    max_reviewing_rounds: int = 1
    termination_phrase: str = "I hereby approve the {goal_noun}"
    fake_performer_request_for_help: str = "Hi {user_skin_name}, could you please help me {goal_verb} a {goal_noun}?"
    fake_reviewer_agree_to_help: str = "Well, I am certainly happy to help guide you and provide some feedback.\n" \
                                       "Please just give me some context first.\n"
    sentence_to_add_at_the_end_of_performer_response: str = \
        'Please provide constructive feedback, or, if you are satisfied, respond with "{termination_phrase}".'

    def __post_init__(self):
        BaseBackgroundProductsGPT.__post_init__(self)
        ReviewDialogDualConverserGPT.__post_init__(self)

    def _add_acknowledgement(self, product_field: str, is_last: bool = False):
        thank_you_message = super()._add_acknowledgement(product_field, is_last=is_last)
        if self.are_we_reviewing_at_all:
            thank_you_message += self.user_initiation_prompt if is_last else ''
            self.apply_to_other_append_surrogate_message(
                content=thank_you_message, tag=f'background_thanks_{product_field}', is_background=True)
        return thank_you_message

    def _add_product_description(self, product_field: str):
        product_description = super()._add_product_description(product_field)
        if self.are_we_reviewing_at_all:
            self.apply_to_other_append_user_message(
                content=product_description, tag=f'background_{product_field}', is_background=True)
        return product_description
