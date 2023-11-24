from dataclasses import dataclass, field
from typing import Dict, List

from stage import DemoStages
from data_to_paper.run_gpt_code.types import CodeAndOutput

from data_to_paper.base_products import Products, NameDescriptionStageGenerator, DataFileDescriptions


@dataclass
class CodingProducts(Products):
    data_file_descriptions: DataFileDescriptions = field(default_factory=DataFileDescriptions)
    codes_and_outputs: List[CodeAndOutput] = field(default_factory=list)

    def _get_generators(self) -> Dict[str, NameDescriptionStageGenerator]:
        return {
            **super()._get_generators(),

            'recent_code': NameDescriptionStageGenerator(
                'Most Recent Code',
                'Here is our most recent Python code:\n```python\n{}\n```\n',
                DemoStages.CODE,
                lambda: self.codes_and_outputs[-1].code,
            ),

        }
