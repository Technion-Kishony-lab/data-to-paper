from dataclasses import dataclass, field
from typing import Optional

from data_to_paper.base_steps.base_steps_runner import BaseStepsRunner
from cast import DemoAgent
from coding_steps import SelfCodeProductsGPT
from products import CodingProducts
from stage import DemoStages


@dataclass
class CodingStepsRunner(BaseStepsRunner):

    cast = DemoAgent
    products: CodingProducts = field(default_factory=CodingProducts)
    research_goal: Optional[str] = None

    def _run_all_steps(self) -> CodingProducts:

        products = self.products  # Start with empty products
        products.data_file_descriptions = self.data_file_descriptions

        # Write code
        self.advance_stage_and_set_active_conversation(DemoStages.CODE, DemoAgent.Debugger)
        SelfCodeProductsGPT.from_(self).get_code_and_output()

        return products
