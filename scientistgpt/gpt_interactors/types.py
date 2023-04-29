from dataclasses import dataclass, field, fields
from typing import Optional, List, Dict, Tuple, Any, Union, Callable

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

    def get_description(self, product_field: str) -> Tuple[str, bool]:
        """
        Return the description of the given product.
        """
        name, description, is_code = PRODUCT_FIELDS_TO_NAME_DESCRIPTION_ISCODE[product_field]
        if isinstance(description, str):
            return description.format(getattr(self, product_field)), is_code
        else:
            return description(self), is_code

    def get_name(self, product_field: str) -> str:
        """
        Return the name of the given product.
        """
        name, description, is_code = PRODUCT_FIELDS_TO_NAME_DESCRIPTION_ISCODE[product_field]
        return name

    @property
    def data_filenames(self) -> List[str]:
        return NiceList([d.file_path for d in self.data_file_descriptions],
                        wrap_with='"',
                        prefix='{} data file[s]: ')


def get_code_description(products: Products) -> str:
    return f'Here is our code:\n\n' \
           f'```python\n{products.code_and_output.code}\n```\n'


def get_code_output_description(products: Products) -> str:
    return f'Here is the output of the code (the content of "{products.code_and_output.output_file}"):\n\n' \
           f'```\n{products.code_and_output.output}\n```\n'


def get_code_and_output_description(products: Products) -> str:
    return get_code_description(products) + '\n\n' + get_code_output_description(products)


PRODUCT_FIELD_NAMES: List[str] = [field.name for field in fields(Products)]

PRODUCT_FIELDS_TO_NAME_DESCRIPTION_ISCODE: Dict[str, Tuple[str, Union[str, Callable], bool]] = {
    'data_file_descriptions': ('dataset', 'DESCRIPTION OF DATASET\n\nWe have the following {}', False),
    'research_goal': ('research goal', 'DESCRIPTION OF OUR RESEARCH GOAL.\n\n{}', False),
    'analysis_plan': ('data analysis plan', 'Here is our data analysis plan:\n\n{}', False),
    'code': ('code', get_code_description, True),
    'code_output': ('output of the code', get_code_output_description, False),
    'code_and_output': ('code and output', get_code_and_output_description, True),

    'result_summary': NotImplemented,
    'implications': NotImplemented,
    'limitations': NotImplemented,
}

