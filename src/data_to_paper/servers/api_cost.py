from __future__ import annotations
from typing import Dict, Optional, Union

from pathlib import Path

from data_to_paper.conversation.stage import Stage
from data_to_paper.servers.json_dump import dump_to_json, load_from_json


class StageToCost(Dict[Optional[Stage], float]):
    """
    A dictionary that stores the api cost for each stage
    key of None is for the total costs of stages that were reset and deleted
    """

    def get_total_cost(self, with_deleted: bool = True) -> float:
        return sum(cost for stage, cost in self.items() if with_deleted or stage is not None)

    def delete_from_stage(self, stage: Stage):
        """
        delete_all_stages_following_stage
        store deleted stage costs in None
        """
        for key in list(self.keys()):
            if key is not None and key >= stage:
                cost = self.pop(key)
                self[None] = self.get(None, 0) + cost

    def save_to_json(self, path: Union[str, Path]):
        """
        Save the api cost to a json file
        Deleted stages are not saved
        """
        as_dict = {stage.value: round(cost, 2) for stage, cost in self.items() if stage is not None}
        dump_to_json(as_dict, path)

    @classmethod
    def load_from_json(cls, path: str) -> StageToCost:
        return cls(load_from_json(path))

    def as_html(self) -> str:
        if not self:
            return '<span style="color: white;">No API usage cost</span>'
        s = '<h2>API usage cost</h2>\n'
        s += '<p>\n'
        s += '<table style="color:white;">\n'
        for stage, cost in self.items():
            if stage is not None:
                s += f'<tr>\n<td>{stage.value}</td>\n<td>${cost:.2f}</td>\n</tr>\n'
        if None in self:
            s += '<tr>\n<td></td>\n<td></td>\n</tr>\n'
            s += f'<tr>\n<td>Deleted stages</td>\n<td>${self[None]:.2f}</td>\n</tr>\n'
        s += '</table>\n'
        s += '</p>\n'
        s += f'<h3>Total cost: ${self.get_total_cost():.2f}</h3>\n'
        return s
