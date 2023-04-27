from dataclasses import dataclass, field, fields
from typing import Optional, List, Dict, Tuple

from scientistgpt.run_gpt_code.code_runner import CodeAndOutput
from scientistgpt.utils.text_utils import NiceList


@dataclass(frozen=True)
class DataFileDescription:
    file_path: str  # relative to the data directory.  should normally just be the file name
    description: str  # a user provided description of the file

    def get_file_header(self, num_lines: int = 4):
        """
        Return the first `num_lines` lines of the file.
        """
        with open(self.file_path) as f:
            head = [next(f) for _ in range(num_lines)]
            return ''.join(head)

    def pretty_repr(self):
        return f'{self.file_path}\n{self.description}\n' \
               f'Here are the first few lines of the file:\n' \
               f'```\n{self.get_file_header()}\n```'


class DataFileDescriptions(List[DataFileDescription]):
    """
    A list of data file descriptions.
    """

    def __str__(self):
        if len(self) == 0:
            s = 'No data files'
        elif len(self) == 1:
            s = "1 data file:\n\n"
            s += self[0].pretty_repr()
        else:
            s = f"{len(self)} data files:\n"
            for file_number, data_file_description in enumerate(self):
                s += f"\n({file_number + 1}) " + data_file_description.pretty_repr()

        return s


@dataclass
class Products:
    """
    Contains the different scientific outcomes of the research.
    These outcomes are gradually populated, where in each step we get a new product based on previous products.
    """
    data_file_descriptions: DataFileDescriptions = field(default_factory=DataFileDescriptions)
    research_goal: Optional[str] = None
    analysis_plan: Optional[str] = None
    code_and_output: CodeAndOutput = field(default_factory=CodeAndOutput)
    result_summary: Optional[str] = None
    implications: Optional[str] = None
    limitations: Optional[str] = None


PRODUCT_FIELD_NAMES: List[str] = [field.name for field in fields(Products)]

PRODUCT_FIELDS_TO_NAME_AND_DESCRIPTIONS: Dict[str, Tuple[str, str]] = {
    'data_file_descriptions': ('dataset', 'DESCRIPTION OF DATASET\n\nWe have the following {}'),
    'research_goal': ('research goal', 'DESCRIPTION OF OUR RESEARCH GOAL.\n\n{}'),
    'analysis_plan': ('data analysisplan', 'Here is our data analysis plan:\n\n{}'),
    'analysis_codes_and_outputs': NotImplemented,
    'result_summary': NotImplemented,
    'implications': NotImplemented,
    'limitations': NotImplemented,
}


@dataclass
class ProductsHolder:
    products: Products = field(default_factory=Products)

    def get_product_description(self, product_field: str) -> str:
        """
        Return the description of the given product.
        """
        return PRODUCT_FIELDS_TO_NAME_AND_DESCRIPTIONS[product_field][1].format(getattr(self.products, product_field))

    def get_product_name(self, product_field: str) -> str:
        """
        Return the name of the given product.
        """
        return PRODUCT_FIELDS_TO_NAME_AND_DESCRIPTIONS[product_field][0]


@dataclass
class CoderProductHolder(ProductsHolder):
    """
    Interact with chatgpt to write a code that needs to create an output file.
    """

    output_filename: str = 'results.txt'
    "The name of the file that gpt code is instructed to save the results to."

    gpt_script_filename: str = 'gpt_code'
    "The base name of the pythin file in which the code written by gpt is saved."

    @property
    def data_filenames(self) -> List[str]:
        return NiceList([d.file_path for d in self.products.data_file_descriptions],
                        wrap_with='"',
                        prefix='{} data file[s]: ')
