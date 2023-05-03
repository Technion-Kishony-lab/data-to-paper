from typing import Any

from scientistgpt.cast import Agent
from scientistgpt.gpt_interactors.step_by_step.base_scientific_conversers import BaseScientificGPT
from scientistgpt.utils.replacer import with_attribute_replacement


class DirectorToStudent(BaseScientificGPT):
    """
    Create a fake (predetermined) conversation, where the Student asks the Director (the application user) for products,
    such as data description, or goal.
    """
    conversation_name: str = 'user-student'
    assistant_agent: Agent = Agent.Director
    user_agent: Agent = Agent.Student

    @with_attribute_replacement
    def get_product_from_director(self, product_field: str, returned_product: Any):
        """
        Ask the user for a product, such as data description, or goal.
        """
        self.initialize_conversation_if_needed()
        product_name = self.products.get_name(product_field)
        self.apply_append_user_message(f'Hi, do you have a {product_name} for me?')
        self.apply_append_surrogate_message(
            f'Yes, here is the {product_name}:\n{returned_product}\n')
        self.apply_append_user_message('Thank you!')
        return returned_product
