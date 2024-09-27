from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from data_to_paper.text import dedent_triple_quote_str
from data_to_paper.utils.nice_list import NiceList

from data_to_paper.base_steps import BaseCodeProductsGPT
from data_to_paper.code_and_output_files.output_file_requirements import TextContentOutputFileRequirement, \
    OutputFileRequirements
from data_to_paper.servers.model_engine import ModelEngine

from .cast import DemoAgent
from .products import DemoProducts


@dataclass
class DemoCodeProductsGPT(BaseCodeProductsGPT):
    model_engine: ModelEngine = ModelEngine.GPT4_TURBO
    products: DemoProducts = None
    assistant_agent: DemoAgent = DemoAgent.Performer
    user_agent: DemoAgent = DemoAgent.Debugger
    background_product_fields: Tuple[str, ...] = ('data_file_descriptions', 'research_goal')
    code_name: str = 'Prime Number Search'

    @property
    def data_filenames(self) -> NiceList[str]:
        return NiceList(self.products.data_file_descriptions.get_data_filenames(),
                        wrap_with='"',
                        prefix='{} data file[s]: ')

    @property
    def data_folder(self) -> Optional[Path]:
        return Path(self.products.data_file_descriptions.data_folder)

    supported_packages: Tuple[str, ...] = ('numpy', )

    mission_prompt: str = dedent_triple_quote_str("""
        Please write a short Python code for the goal above.

        Your code should create the following output files: {requested_output_filenames}.
        These files should contain ...

        If needed, you can use the following packages which are already installed:
        {supported_packages}
        """)

    def _create_output_file_requirements(self) -> OutputFileRequirements:
        return OutputFileRequirements([TextContentOutputFileRequirement('output.txt')])
