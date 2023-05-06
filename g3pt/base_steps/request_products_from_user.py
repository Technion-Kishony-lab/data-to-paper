from dataclasses import dataclass
from typing import Any

from g3pt.utils.replacer import with_attribute_replacement

from .base_products_conversers import BaseProductsGPT


@dataclass
class DirectorProductGPT(BaseProductsGPT):
    """
    Create a fake (pre-meditated) conversation, where a performer asks the Director (the application user) for a
    specific product.
    """
    ADDITIONAL_DICT_ATTRS = ('product_name', )

    request_product_message: str = 'Hi, do you have a {product_name} for me?'
    provide_product_message: str = 'Yes, here is the {product_name}:\n{returned_product}\n'
    thanks_message: str = 'Thank you!'

    # inputs:
    product_field: str = None
    returned_product: Any = None

    @property
    def product_name(self):
        return self.products.get_name(self.product_field) if self.product_field is not None else None

    @with_attribute_replacement
    def get_product_from_director(self, **kwargs):
        """
        Ask the user for a product, such as data description, or goal.
        """
        self.set(**kwargs)
        self.initialize_conversation_if_needed()
        self.apply_append_user_message(self.request_product_message)
        self.apply_append_surrogate_message(self.provide_product_message)
        self.apply_append_user_message(self.thanks_message)
        return self.returned_product
