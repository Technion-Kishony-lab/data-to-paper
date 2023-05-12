from dataclasses import dataclass

from .actions_and_conversations import Action
from ..base_cast import Agent
from ..base_steps import Products
from ..utils import format_text_with_code_blocks


class Stage:
    """
    Store a class attribute that designates each stage in the process.
    """
    FINISHED = "finished"
    FAILURE = "failure"


@dataclass(frozen=True)
class MessengerAction(Action):
    def apply_to_web(self) -> bool:
        return True


@dataclass(frozen=True)
class StageAction(MessengerAction):
    stage: Stage = None

    def _pretty_attrs(self) -> str:
        return f'{self.stage}'


@dataclass(frozen=True)
class AdvanceStage(StageAction):
    pass


@dataclass(frozen=True)
class SetProduct(StageAction):
    products: Products = None
    product_field: str = None

    def get_product_description(self) -> str:
        return format_text_with_code_blocks(
            text=self.products.get_description(product_field=self.product_field),
            is_html=True)

    def _pretty_attrs(self) -> str:
        return f'{self.stage}, {self.product_field}'


@dataclass(frozen=True)
class SetActiveConversation(MessengerAction):
    agent: Agent = None

    @property
    def conversation_name(self) -> str:
        return self.agent.get_conversation_name()

    def _pretty_attrs(self) -> str:
        return f'{self.conversation_name}'
