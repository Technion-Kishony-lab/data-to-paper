from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from data_to_paper.base_steps import BaseCodeProductsGPT
from data_to_paper.projects.demo_project.cast import DemoAgent
from data_to_paper.projects.demo_project.products import DemoProducts

from data_to_paper.utils import dedent_triple_quote_str
from data_to_paper.utils.nice_list import NiceList


@dataclass
class DemoCodeProductsGPT(BaseCodeProductsGPT):
    products: DemoProducts = None
    assistant_agent: DemoAgent = DemoAgent.Performer
    user_agent: DemoAgent = DemoAgent.Debugger
    allow_data_files_from_sections: Tuple[Optional[str]] = (None, )  # None for the raw data files, () for no data files
    background_product_fields: Tuple[str, ...] = ('data_file_descriptions', 'research_goal')
    gpt_script_filename: str = None
    code_name: str = 'Prime Number Search'

    @property
    def data_filenames(self) -> NiceList[str]:
        return NiceList(self.products.data_file_descriptions.get_data_filenames(),
                        wrap_with='"',
                        prefix='{} data file[s]: ')

    @property
    def data_folder(self) -> Optional[Path]:
        return Path(self.products.data_file_descriptions.data_folder)

    output_filename: str = 'prime_number.txt'
    allowed_created_files: Tuple[str, ...] = ()
    allow_dataframes_to_change_existing_series = False
    enforce_saving_altered_dataframes: bool = False

    supported_packages: Tuple[str, ...] = ('numpy', )

    user_initiation_prompt: str = dedent_triple_quote_str("""
        Please write a short Python code for finding the largest number below our chosen max number.

        Your code should create an output text file named "{output_filename}", which should \
        contain the following text:
        "The largest prime number below xxx is yyy".

        If needed, you can use the following packages which are already installed:
        {supported_packages}
        """)
