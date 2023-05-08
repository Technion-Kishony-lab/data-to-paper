from dataclasses import dataclass

from .actions import Action, apply_action


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


def append_advance_stage(stage: Stage):
    """
    Append an action to advance the stage of the process.
    """
    apply_action(AdvanceStage(stage=stage))
