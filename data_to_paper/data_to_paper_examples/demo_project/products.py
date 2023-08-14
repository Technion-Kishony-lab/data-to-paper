from dataclasses import dataclass, field
from typing import Optional, Dict

from stage import DemoStages
from data_to_paper.run_gpt_code.types import CodeAndOutput

from data_to_paper.base_products import Products, NameDescriptionStageGenerator, DataFileDescriptions


@dataclass
class DemoProducts(Products):
    """
    Contains the different scientific outcomes of the research.
    These outcomes are gradually populated, where in each step we get a new product based on previous products.
    """
    data_file_descriptions: DataFileDescriptions = field(default_factory=DataFileDescriptions)
    research_goal: Optional[str] = None
    code_and_output: CodeAndOutput = None
    paper_sections: Dict[str, str] = field(default_factory=dict)

    def _get_generators(self) -> Dict[str, NameDescriptionStageGenerator]:
        return {
            **super()._get_generators(),

            'data_file_descriptions': NameDescriptionStageGenerator(
                'Input file',
                'Input Files\n\n{}',
                DemoStages.DATA,
                lambda: self.data_file_descriptions,
            ),

            'research_goal': NameDescriptionStageGenerator(
                'Research Goal',
                'Here is our Research Goal\n\n{}',
                DemoStages.GOAL,
                lambda: self.research_goal,
            ),

            'code': NameDescriptionStageGenerator(
                'Prime-Finding Code',
                'Here is our Python code to find the largest prime below the given number:\n```python\n{}\n```\n',
                DemoStages.CODE,
                lambda: self.code_and_output.code,
            ),

            'output': NameDescriptionStageGenerator(
                'Output of the code',
                'Here is the output of our code:\n```output\n{}\n```\n',
                DemoStages.CODE,
                lambda: self.code_and_output.output,
            ),

            'code_and_output': NameDescriptionStageGenerator(
                'Code and Output',
                '{code_description}\n\n{output_description}',
                DemoStages.CODE,
                lambda: {
                    'code_description': self.get_description("code"),
                    'output_description': self.get_description("output")},
            ),

            'paper_sections': NameDescriptionStageGenerator(
                'Paper Sections',
                'Here are the paper sections:\n```output\n{paper}\n```\n',
                DemoStages.WRITING,
                lambda: {'paper': self.paper_sections},
            ),
        }
