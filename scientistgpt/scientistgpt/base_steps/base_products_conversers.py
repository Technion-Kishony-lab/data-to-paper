from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Optional

from scientistgpt.base_products import Products
from .result_converser import ResultConverser
from .dual_converser import ReviewDialogDualConverserGPT
from scientistgpt.utils import dedent_triple_quote_str
from scientistgpt.utils.copier import Copier
from scientistgpt.utils.nice_list import NiceList
from scientistgpt.utils.check_numeric_values import find_non_matching_numeric_values
from ..utils.highlighted_text import print_red


@dataclass
class ProductsHandler(Copier):
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
class ProductsConverser(ProductsHandler, ResultConverser):
    COPY_ATTRIBUTES = ProductsHandler.COPY_ATTRIBUTES | ResultConverser.COPY_ATTRIBUTES

    def __post_init__(self):
        ProductsHandler.__post_init__(self)
        ResultConverser.__post_init__(self)


@dataclass
class BackgroundProductsConverser(ProductsConverser):
    """
    Base class for conversers that deal with Products.
    Allows for the addition of background information about prior products to the conversation.
    """
    background_product_fields: Tuple[str] = None
    # tuple of product fields to provide background information about.
    # If empty tuple, do not provide background information.
    # if None, this instance was called into an already running conversation by another converser
    # and should not add any new background information.

    product_acknowledgement: str = "Thank you for the {}. \n"
    goal_noun: str = None
    goal_verb: str = None
    fake_performer_request_for_help: str = \
        "Hi {user_skin_name}, I need to {goal_verb} a {goal_noun}. Could you please guide me?"
    fake_reviewer_agree_to_help: str = dedent_triple_quote_str("""
        Sure, I am happy to guide you {goal_verb} the {goal_noun} and can also provide feedback.

        Note that your {goal_noun} should be based on the following research products that you have now \
        already obtained:
        ```highlight
        {vertical_actual_background_product_names}
        ```
        Please carefully review these intermediate products and then proceed according to my guidelines below. 
        """)
    post_background_comment: str = 'Background messages completed. Requesting "{goal_noun}".'

    @property
    def actual_background_product_fields(self) -> Optional[Tuple[str, ...]]:
        if self.background_product_fields is None:
            return None
        return self._get_available_background_product_fields(self.background_product_fields)

    def _get_available_background_product_fields(self, product_fields: Tuple[str, ...]) -> Tuple[str, ...]:
        return tuple(product_field for product_field in product_fields
                     if self.products.is_product_available(product_field))

    @property
    def background_product_names(self) -> NiceList[str]:
        return NiceList((self.products.get_name(product_field)
                         for product_field in self.actual_background_product_fields),
                        wrap_with='"', separator=', ', last_separator=' and ')

    @property
    def actual_background_product_names(self) -> NiceList:
        if not self.actual_background_product_fields:
            return NiceList()
        return NiceList(
            [self.products.get_name(product_field) for product_field in self.actual_background_product_fields],
            wrap_with='"', separator=', ', empty_str='')

    @property
    def vertical_actual_background_product_names(self) -> NiceList:
        return NiceList([name for name in self.actual_background_product_names],
                        wrap_with='', separator='\n', empty_str='NO BACKGROUND PRODUCTS')

    def _get_acknowledgement_and_tag(self, product_field: str) -> Tuple[str, str]:
        thank_you_message = self.product_acknowledgement.format(self.products.get_name(product_field))
        tag = f'background_thanks_{product_field}'
        return thank_you_message, tag

    def get_product_description_and_tag(self, product_field: str) -> Tuple[str, str]:
        product_description = self.products.get_description(product_field)
        tag = f'background_{product_field}'
        return product_description, tag

    def _add_acknowledgement(self, product_field: str, is_last: bool = False):
        acknowledgement, tag = self._get_acknowledgement_and_tag(product_field)
        self.apply_append_surrogate_message(acknowledgement, tag=tag, is_background=True, reverse_roles_for_web=True)

    def _add_product_description(self, product_field: str):
        product_description, tag = self.get_product_description_and_tag(product_field)
        self.apply_append_user_message(product_description, tag=tag, is_background=True, reverse_roles_for_web=True)

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
        previous_product_items = self.actual_background_product_fields
        if previous_product_items is not None:
            assert len(self.conversation) == 1
            self._add_fake_pre_conversation_exchange()
            for i, product_field in enumerate(previous_product_items or []):
                is_last = i == len(previous_product_items) - 1
                self._add_product_description(product_field)
                self._add_acknowledgement(product_field, is_last=is_last)
            if self.post_background_comment:
                self.comment(self.post_background_comment, tag='after_background', web_conversation_name=None)
        return super()._pre_populate_background()


@dataclass
class ReviewBackgroundProductsConverser(BackgroundProductsConverser, ReviewDialogDualConverserGPT):
    """
    Base class for conversers that specify prior products and then set a goal for the new product
    to be suggested and reviewed.
    """
    COPY_ATTRIBUTES = BackgroundProductsConverser.COPY_ATTRIBUTES | ReviewDialogDualConverserGPT.COPY_ATTRIBUTES
    suppress_printing_other_conversation: bool = False
    max_reviewing_rounds: int = 1
    termination_phrase: str = "I hereby approve the {goal_noun}"
    sentence_to_add_at_the_end_of_performer_response: str = \
        'Please provide constructive feedback, or, if you are satisfied, respond with "{termination_phrase}".'

    def __post_init__(self):
        BackgroundProductsConverser.__post_init__(self)
        ReviewDialogDualConverserGPT.__post_init__(self)

    def _pre_populate_other_background(self):
        previous_product_items = self.actual_background_product_fields
        if previous_product_items is not None:
            assert len(self.other_conversation) == 1
            for i, product_field in enumerate(previous_product_items or []):
                is_last = i == len(previous_product_items) - 1
                self._add_other_product_description(product_field)
                self._add_other_acknowledgement(product_field, is_last=is_last)
        return super()._pre_populate_other_background()

    def _add_other_acknowledgement(self, product_field: str, is_last: bool = False):
        acknowledgement, tag = self._get_acknowledgement_and_tag(product_field)
        acknowledgement += self.user_initiation_prompt if is_last else ''
        self.apply_to_other_append_surrogate_message(acknowledgement, tag=tag, is_background=True)

    def _add_other_product_description(self, product_field: str):
        product_description, tag = self.get_product_description_and_tag(product_field)
        self.apply_to_other_append_user_message(product_description, tag=tag, is_background=True)


class CheckExtractionReviewBackgroundProductsConverser(ReviewBackgroundProductsConverser):
    product_fields_from_which_response_is_extracted: Tuple[str] = None

    def _get_text_from_which_response_should_be_extracted(self) -> str:
        return '\n'.join(self.products.get_description(product_field)
                         for product_field in self.product_fields_from_which_response_is_extracted)

    @property
    def names_of_products_from_which_to_extract(self) -> List[str]:
        return NiceList(self.products.get_name(product_field)
                        for product_field in self.product_fields_from_which_response_is_extracted)

    def _check_extracted_text(self, text: str):
        if text not in self._get_text_from_which_response_should_be_extracted():
            self._raise_self_response_error(
                f'"{text}" is not an explicit extraction from the provided '
                f'{self.names_of_products_from_which_to_extract}.')

    def _check_extracted_numbers(self, text: str,
                                 just_warn: bool = False,
                                 ignore_int_below: int = 20,
                                 remove_trailing_zeros: bool = True,
                                 allow_truncating: bool = True):
        non_matching = find_non_matching_numeric_values(source=self._get_text_from_which_response_should_be_extracted(),
                                                        target=text, ignore_int_below=ignore_int_below,
                                                        remove_trailing_zeros=remove_trailing_zeros,
                                                        ignore_one_with_zeros=True, ignore_after_smaller_than_sign=True,
                                                        allow_truncating=allow_truncating)
        if non_matching:
            if just_warn:
                print_red('########################')
                print_red('####### WARNING: #######')
                print_red('########################')
                print_red(f'Some of the specified values {non_matching} are not explicitly extracted from:\n'
                          f'{self.names_of_products_from_which_to_extract}.')
            else:
                self._raise_self_response_error(
                    f'Some of the specified values {non_matching} are not explicitly extracted from the provided '
                    f'{self.names_of_products_from_which_to_extract}.')
