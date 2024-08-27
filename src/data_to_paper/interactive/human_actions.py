from dataclasses import dataclass

from data_to_paper.utils.serialize import SerializableValue


@dataclass
class HumanAction(SerializableValue):
    """
    Class to store human actions.
    """
    pass


@dataclass
class ButtonClickedHumanAction(HumanAction):
    """
    Class to store human actions of clicking a button.
    value: str - the name of the button.
    """
    pass


@dataclass
class TextSentHumanAction(HumanAction):
    """
    Class to store human actions of sending text.
    value: str - the text sent.
    """
    pass


@dataclass
class RequestInfoHumanAction(HumanAction):
    """
    Class to store human actions of requesting missing text.
    """
    pass
