from typing import Dict, Any, Union, List

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


def get_all_keys_following_stage(data: Dict[Union[Stage, str], Any], stage: Stage,
                                 include_stage: bool = True
                                 ) -> List[Union[Stage, str]]:
    """
    Get all the keys of data that are following the given stage
    keys can be either Stage or str
    """
    stage_cls = stage.__class__
    keys = []
    for key in list(data.keys()):
        if isinstance(key, str):
            for stage_name in stage_cls:
                if stage_name.value == key:
                    current_stage = stage_name
                    break
            else:
                raise ValueError(f"Stage {key} not found in {stage_cls}")
        else:
            current_stage = key
        if (isinstance(current_stage, stage_cls) and
                (current_stage > stage or (include_stage and current_stage == stage))):
            keys.append(key)
    return keys


def delete_all_stages_following_stage(data: Dict[Union[Stage, str], Any], delete_from_stage: Stage,
                                      include_stage: bool = True):
    """
    Delete all stages following the given stage
    """
    keys = get_all_keys_following_stage(data, delete_from_stage, include_stage)
    for key in keys:
        del data[key]
