from dataclasses import dataclass
from typing import Any

from scientistgpt.utils.replacer import with_attribute_replacement

from .base_products_conversers import BaseProductsGPT


@dataclass
class DirectorProductGPT(BaseProductsGPT):
    """
    Create a fake (pre-meditated) conversation, where a performer asks the Director (the application user) for a
    specific product.
    """
    ADDITIONAL_DICT_ATTRS = ('product_name', )

    system_prompt: str = None
    request_product_message: str = 'Hi, do you have a {product_name} for me?'
    provide_product_message: str = 'Yes, here is the {product_name}:\n{returned_product}\n'
    thanks_message: str = 'Thank you!'

    no_product_message: str = 'No, I do not have a {product_name} for you.'
    acknowledge_no_product_message: str = 'Ok, thank you for letting me know.'

    # inputs:
    product_field: str = None
    returned_product: Any = None

    @property
    def product_name(self):
        return self.products.get_name(self.product_field) if self.product_field is not None else None

    def _get_product_from_director(self):
        """
        Ask the user for a product, such as data description, or goal.
        """
        self.apply_append_surrogate_message(self.provide_product_message)
        self.apply_append_user_message(self.thanks_message)
        return self.returned_product

    def _get_no_product(self):
        self.apply_append_surrogate_message(self.no_product_message)
        self.apply_append_user_message(self.acknowledge_no_product_message)
        return None

    @with_attribute_replacement
    def get_product_or_no_product_from_director(self, **kwargs):
        """
        Ask the user for a product, such as data description, or goal.
        """
        self.set(**kwargs)
        self.initialize_conversation_if_needed()
        self.apply_append_user_message(self.request_product_message)
        if self.returned_product is None:
            return self._get_no_product()
        else:
            return self._get_product_from_director()
