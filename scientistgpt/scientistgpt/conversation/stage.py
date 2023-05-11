from dataclasses import dataclass

from .actions_and_conversations import Action


class Stage:
    """
    Store a class attribute that designates each stage in the process.
    """
    pass


@dataclass(frozen=True)
class StageAction(Action):
    stage: Stage = None

    def _pretty_attrs(self) -> str:
        return f'{self.stage}'

    def apply_to_web(self) -> bool:
        return True


@dataclass(frozen=True)
class AdvanceStage(StageAction):
    pass


@dataclass(frozen=True)
class SetActiveConversation(Action):
    conversation_name: str = None

    def _pretty_attrs(self) -> str:
        return f'{self.conversation_name}'
