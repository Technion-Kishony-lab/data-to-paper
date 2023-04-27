from dataclasses import dataclass, field, fields
from typing import Optional, List

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
    analysis_codes_and_outputs: List[CodeAndOutput] = field(default_factory=list)
    result_summary: Optional[str] = None
    implications: Optional[str] = None
    limitations: Optional[str] = None


PRODUCT_FIELD_NAMES: List[str] = [field.name for field in fields(Products)]





@dataclass
class ProductsHolder:
    products: Products = field(default_factory=Products)

    @property
    def number_of_successful_code_revisions(self):
        return len(self.products.analysis_codes_and_outputs)


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
    def gpt_script_revision_file_name(self):
        return f"{self.gpt_script_filename}_revision{self.number_of_successful_code_revisions}"

    @property
    def data_filenames(self) -> List[str]:
        return NiceList([d.file_path for d in self.products.data_file_descriptions],
                        wrap_with='"',
                        prefix='{} data file[s]: ')

    def get_output_filename(self, after_completion: bool = False, revision_number: Optional[int] = None):
        revision_number = self.number_of_successful_code_revisions if revision_number is None else revision_number
        if after_completion:
            revision_number -= 1
        if revision_number == 0:
            return self.output_filename
        return self.output_filename.replace('.', f'_revision_{revision_number}.')
