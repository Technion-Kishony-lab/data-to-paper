from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from scientistgpt.base_steps import BaseCodeProductsGPT
from scientistgpt.projects.scientific_research.cast import ScientificAgent
from scientistgpt.projects.scientific_research.scientific_products import ScientificProducts
from scientistgpt.utils import dedent_triple_quote_str
from scientistgpt.utils.text_utils import NiceList


@dataclass
class ScientificCodeProductsGPT(BaseCodeProductsGPT):
    products: ScientificProducts = None
    background_product_fields = ('data_file_descriptions', 'research_goal', 'analysis_plan')
    conversation_name: str = 'code_debugging'
    assistant_agent: ScientificAgent = ScientificAgent.Performer
    user_agent: ScientificAgent = ScientificAgent.Debugger
    code_requesting_prompt: str = BaseCodeProductsGPT.code_requesting_prompt + dedent_triple_quote_str("""
        All results we may need for a scientific paper should be saved to this text file, including \
        analysis results, summary statistics, etc. Do not write to any other files.
        Do not create any graphics, figures or any plots.
        """)
    requesting_code_explanation_prompt: str = dedent_triple_quote_str("""
        Please explain what your code does. Do not provide a line-by-line explanation, rather provide a \
        high-level explanation of the code in a language suitable for a Methods section of a research \
        paper. Also explain what does the code writes into the {} file.
        """)

    @property
    def data_filenames(self) -> NiceList[str]:
        return NiceList(self.products.data_file_descriptions.get_data_filenames(),
                        wrap_with='"',
                        prefix='{} data file[s]: ')

    @property
    def data_folder(self) -> Optional[Path]:
        return Path(self.products.data_file_descriptions.data_folder)
