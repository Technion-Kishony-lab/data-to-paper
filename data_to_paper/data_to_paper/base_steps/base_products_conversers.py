from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Optional

from data_to_paper.base_products import Products
from .result_converser import ResultConverser, Rewind
from .dual_converser import ReviewDialogDualConverserGPT
from data_to_paper.utils import dedent_triple_quote_str
from data_to_paper.utils.copier import Copier
from data_to_paper.utils.nice_list import NiceList
from data_to_paper.utils.replacer import Replacer, StrOrReplacer
from data_to_paper.utils.types import ListBasedSet
from data_to_paper.utils.check_numeric_values import find_non_matching_numeric_values
from data_to_paper.conversation import Message, GeneralMessageDesignation

from data_to_paper.servers.openai_models import ModelEngine


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
    background_product_fields: Tuple[str, ...] = None
    # tuple of product fields to provide background information about.
    # If empty tuple, do not provide background information.
    # if None, this instance was called into an already running conversation by another converser
    # and should not add any new background information.
    background_product_fields_to_hide: Tuple[str, ...] = None

    product_acknowledgement: str = "Thank you for the {}. \n"
    goal_noun: str = None
    goal_verb: str = None
    fake_performer_request_for_help: str = \
        "Hi {user_skin_name}, I need to {goal_verb} {goal_noun}. Could you please guide me?"
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
    def replacer_kwargs(self):
        if self.background_product_fields is None:
            return {}
        return {field: self.products[field].name for field in self.background_product_fields
                if self.products.is_product_available(field)}

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

    def _get_product_tags(self, product_field: str) -> Tuple[str, str]:
        return f'background_{product_field}', f'background_thanks_{product_field}',

    def _get_acknowledgement_and_tag(self, product_field: str) -> Tuple[str, str]:
        thank_you_message = self.product_acknowledgement.format(self.products.get_name(product_field))
        _, tag = self._get_product_tags(product_field)
        return thank_you_message, tag

    def get_product_description_and_tag(self, product_field: str) -> Tuple[str, str]:
        product_description = self.products.get_description(product_field)
        tag, _ = self._get_product_tags(product_field)
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
            assert len(self.conversation.get_chosen_messages()) == 1
            self._add_fake_pre_conversation_exchange()
            for i, product_field in enumerate(previous_product_items or []):
                is_last = i == len(previous_product_items) - 1
                self._add_product_description(product_field)
                self._add_acknowledgement(product_field, is_last=is_last)
            if self.post_background_comment:
                self.comment(self.post_background_comment, tag='after_background', web_conversation_name=None)
        return super()._pre_populate_background()

    def apply_get_and_append_assistant_message(self, tag: Optional[StrOrReplacer] = None,
                                               comment: Optional[StrOrReplacer] = None,
                                               is_code: bool = False, previous_code: Optional[str] = None,
                                               model_engine: Optional[ModelEngine] = None,
                                               hidden_messages: GeneralMessageDesignation = None,
                                               expected_tokens_in_response: int = None,
                                               background_product_fields_to_hide: Optional[Tuple[str, ...]] = None,
                                               **kwargs) -> Message:
        """
        Apply get and append assistant message.
        Allows hiding specific background product fields.
        """
        background_product_fields_to_hide = background_product_fields_to_hide or self.background_product_fields_to_hide
        if hidden_messages is None and background_product_fields_to_hide:
            hidden_messages = []
            for product_field in background_product_fields_to_hide:
                product_tag, thanks_tag = self._get_product_tags(product_field)
                hidden_messages.append(product_tag)
                hidden_messages.append(thanks_tag)

        return super().apply_get_and_append_assistant_message(
            tag=tag, comment=comment, is_code=is_code, previous_code=previous_code,
            model_engine=model_engine, hidden_messages=hidden_messages,
            expected_tokens_in_response=expected_tokens_in_response, **kwargs)


@dataclass
class ReviewBackgroundProductsConverser(BackgroundProductsConverser, ReviewDialogDualConverserGPT):
    """
    Base class for conversers that specify prior products and then set a goal for the new product
    to be suggested and reviewed.
    """
    COPY_ATTRIBUTES = BackgroundProductsConverser.COPY_ATTRIBUTES | ReviewDialogDualConverserGPT.COPY_ATTRIBUTES
    suppress_printing_other_conversation: bool = False
    max_reviewing_rounds: int = 1
    termination_phrase: str = "The {goal_noun} does not require any changes"
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
        acknowledgement += f'\n{self.user_initiation_prompt}' if is_last else ''
        self.apply_to_other_append_surrogate_message(acknowledgement, tag=tag, is_background=True)

    def _add_other_product_description(self, product_field: str):
        product_description, tag = self.get_product_description_and_tag(product_field)
        self.apply_to_other_append_user_message(product_description, tag=tag, is_background=True)


class CheckExtractionReviewBackgroundProductsConverser(ReviewBackgroundProductsConverser):
    product_fields_from_which_response_is_extracted: Tuple[str, ...] = None
    only_warn_about_non_matching_values: bool = False

    _number_of_non_matching_values: int = None

    warning_about_non_matching_values: str = dedent_triple_quote_str("""
        ########################
        ####### WARNING: #######
        ########################
        Some of the specified values {} are not explicitly extracted from:
        {names_of_products_from_which_to_extract}
        """)

    report_non_match_prompt: str = dedent_triple_quote_str("""
        Any numeric value in your section must be based on the `provided data` above, namely on numerical values \
        extracted from: 
        {names_of_products_from_which_to_extract}
        
        However, upon reviewing your section, I've identified certain `potentially problematic values`, \
        which don't directly match the `provided data`. They are: 
        {}
        
        For transparency, please revise your section such that it includes only values \
        explicitly extracted from the `provided data` above, or derived from them using the `\\num{<formula>}` syntax. 

        Examples:
        - If you would like to report the difference between two provided values 87 and 65, you should write:
        "The initial price of 87 was changed to 65, representing a difference of \\num{87 - 65}"

        - If you would like to report the odds ratio corresponding to a provided regression coefficient of 1.234, \
        you should write:
        "The regression coefficient was 1.234 corresponding to an odds ratio of \\num{exp(1.234)}"

        - If the provided data includes a distance of 9.1e3 cm, and you would like to report the distance in meters, \
        you should write: 
        "Our analysis revealed a distance of \\num{9.1e3 / 100} meters"
        
        IMPORTANT NOTE:
        If we need to include a numeric value that was not calculated or is not explicitly given in the \
        Tables or "{additional_results}", \
        and cannot be derived from them, \
        then indicate `[unknown]` instead of the numeric value. 
        
        For example:
        
        "The regression coefficient for the anti-cancer drugs was [unknown]."
        """)

    def _get_text_from_which_response_should_be_extracted(self) -> str:
        return '\n'.join(self.products.get_description(product_field)
                         for product_field in self.product_fields_from_which_response_is_extracted
                         if self.products.is_product_available(product_field))

    @property
    def names_of_products_from_which_to_extract(self) -> List[str]:
        return NiceList((self.products.get_name(product_field)
                        for product_field in self.product_fields_from_which_response_is_extracted),
                        wrap_with='"',
                        last_separator=' and ')

    def _check_extracted_numbers(self, text: str,
                                 ignore_int_below: int = 100,
                                 remove_trailing_zeros: bool = True,
                                 allow_truncating: bool = True):
        if self.product_fields_from_which_response_is_extracted is None:
            return

        # Find the non-matching values:
        non_matching, matching = find_non_matching_numeric_values(
            source=self._get_text_from_which_response_should_be_extracted(),
            target=text,
            ignore_int_below=ignore_int_below,
            remove_trailing_zeros=remove_trailing_zeros,
            ignore_one_with_zeros=True, ignore_after_smaller_than_sign=True,
            allow_truncating=allow_truncating)
        number_of_non_matching_values, number_of_matching_values = len(non_matching), len(matching)
        if self._number_of_non_matching_values is None:
            add_iterations = 3  # first time, we start with added 3 iterations
        else:
            add_iterations = int(number_of_non_matching_values < self._number_of_non_matching_values)

        # Print to the console the number of non-matching values:
        self.comment(f'Checking {number_of_matching_values + number_of_non_matching_values} numerical values. '
                     f'Found {number_of_non_matching_values} non-matching.', as_action=False)
        if self._number_of_non_matching_values is not None:
            self.comment(f'Compared to {self._number_of_non_matching_values} non-matching in the previous iteration '
                         f'(add_iterations: {add_iterations})', as_action=False)
        self._number_of_non_matching_values = number_of_non_matching_values
        if non_matching:
            if self.only_warn_about_non_matching_values:
                self.comment(Replacer(self, self.warning_about_non_matching_values, args=(non_matching,)),
                             as_action=False)
            else:
                self._raise_self_response_error(
                    Replacer(self, self.report_non_match_prompt, args=(ListBasedSet(non_matching),)),
                    rewind=Rewind.REPOST_AS_FRESH,
                    add_iterations=add_iterations,
                    bump_model=True,
                )

    def _check_url_in_text(self, text: str) -> str:
        """
        Check that the text does not contain a URL. If it does raise an error.
        """
        if 'http' in text or 'www.' in text or 'mailto' in text:
            self._raise_self_response_error(
                'The text contains a URL which is not allowed.',
                rewind=Rewind.REPOST_AS_FRESH,
            )
        return text
