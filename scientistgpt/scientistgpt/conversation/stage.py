from dataclasses import dataclass

from .actions import Action, apply_action


class Stage:
    """
    Store a class attribute that designates each stage in the process.
    """
    pass


@dataclass(frozen=True)
class AdvanceStage(Action):
    stage: Stage = None

    def _pretty_attrs(self) -> str:
        return f'{self.stage}'


def append_advance_stage(stage: Stage):
    """
    Append an action to advance the stage of the process.
    """
    apply_action(AdvanceStage(stage=stage, conversation_name='null', driver='null'))
