from dataclasses import dataclass, field
from typing import Optional, Dict

from data_to_paper.code_and_output_files.code_and_output import CodeAndOutput
from data_to_paper.base_products import Products, NameDescriptionStageGenerator
from data_to_paper.base_products.file_descriptions import DataFileDescriptions

from .stage import DemoStages


@dataclass
class DemoProducts(Products):
    """
    All the products generated in the demo.
    """
    data_file_descriptions: DataFileDescriptions = field(default_factory=DataFileDescriptions)
    research_goal: Optional[str] = None
    code_and_output: CodeAndOutput = None
    paper_sections: Dict[str, str] = field(default_factory=dict)

    def _get_generators(self) -> Dict[str, NameDescriptionStageGenerator]:
        return {
            **super()._get_generators(),

            'data_file_descriptions': NameDescriptionStageGenerator(
                'Data File Descriptions',
                '{}',
                DemoStages.DATA,
                lambda: self.data_file_descriptions,
            ),

            'research_goal': NameDescriptionStageGenerator(
                'Research Goal',
                '{}',
                DemoStages.GOAL,
                lambda: self.research_goal,
            ),

            'code_and_output': NameDescriptionStageGenerator(
                'Code and Output',
                '{description}',
                DemoStages.CODE,
                lambda: {
                    'description': self.code_and_output.to_text(with_header=False)},
            ),

            'title_and_abstract': NameDescriptionStageGenerator(
                'Title and Abstract',
                "```latex\n{}\n\n{}```",
                DemoStages.WRITING,
                lambda: (self.paper_sections['title'],
                         self.paper_sections['abstract']),
            ),
        }
