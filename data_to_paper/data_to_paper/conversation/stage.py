from data_to_paper.utils.types import IndexOrderedEnum


class Stage(IndexOrderedEnum):
    """
    Define the sequence of stages
    Each stage is defined as (str, bool),
    indicating the name of the stage and whether the user
    can reset to this stage.
    """

    def __new__(cls, value, resettable):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.resettable = resettable
        return obj
