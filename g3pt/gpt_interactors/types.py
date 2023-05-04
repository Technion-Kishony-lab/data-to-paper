from dataclasses import dataclass, field, fields
from typing import Optional, List, Dict, Tuple, Union, Callable, Set

from g3pt.gpt_interactors.citation_adding.call_crossref import CrossrefCitation
from g3pt.run_gpt_code.code_runner import CodeAndOutput
from g3pt.utils.text_utils import NiceList, dedent_triple_quote_str


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
    results_summary: Optional[str] = None
    paper_sections: Dict[str, str] = field(default_factory=dict)
    cited_paper_sections: Dict[str, Tuple[str, Set[CrossrefCitation]]] = field(default_factory=dict)
    paper_sections_with_tables: Dict[str, str] = field(default_factory=dict)

    def get_description(self, product_field: str) -> str:
        """
        Return the description of the given product.
        """
        name, description = get_name_description_iscode(product_field)
        if isinstance(description, str):
            return description.format(getattr(self, product_field))
        else:
            return description(self)

    def get_name(self, product_field: str) -> str:
        """
        Return the name of the given product.
        """
        name, description = get_name_description_iscode(product_field)
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


def get_title_and_abstract_description(products: Products) -> str:
    return dedent_triple_quote_str("""
    Here are the title and abstract of the paper:

        {}

        {}
        """).format(products.paper_sections['title'], products.paper_sections['abstract'])


def format_paper_section_description(section_content: str, section_name: str) -> str:
    return dedent_triple_quote_str("""
        Here is the "{}" section of the paper:

        {}
        """).format(section_name, section_content)


def get_paper_section_description(products: Products, section_name: str) -> str:
    return format_paper_section_description(products.paper_sections[section_name], section_name)


def get_paper_section_with_citations_description(products: Products, section_name: str) -> str:
    return format_paper_section_description(products.cited_paper_sections[section_name][0], section_name)


def get_paper_section_with_table_description(products: Products, section_name: str) -> str:
    return format_paper_section_description(products.paper_sections_with_tables[section_name], section_name)


def get_paper_section_most_updated(products: Products, section_name: str) -> str:
    if section_name in products.paper_sections_with_tables:
        return format_paper_section_description(products.paper_sections_with_tables[section_name], section_name)
    if section_name in products.cited_paper_sections:
        return format_paper_section_description(products.cited_paper_sections[section_name][0], section_name)
    if section_name in products.paper_sections:
        return format_paper_section_description(products.paper_sections[section_name], section_name)
    assert False, f'No section named "{section_name}"'


PRODUCT_FIELD_NAMES: List[str] = [field.name for field in fields(Products)]

PRODUCT_FIELDS_TO_NAME_DESCRIPTION_ISCODE: Dict[str, Tuple[str, Union[str, Callable]]] = {
    'data_file_descriptions': ('dataset', 'DESCRIPTION OF DATASET\n\nWe have the following {}'),
    'research_goal': ('research goal', 'DESCRIPTION OF OUR RESEARCH GOAL.\n\n{}'),
    'analysis_plan': ('data analysis plan', 'Here is our data analysis plan:\n\n{}'),
    'code': ('code', get_code_description),
    'code_output': ('output of the code', get_code_output_description),
    'code_and_output': ('code and output', get_code_and_output_description),
    'results_summary': ('results summary', 'Here is a summary of our results:\n\n{}'),
    'title_and_abstract': ('title and abstract', get_title_and_abstract_description),
}

SECTION_TYPES_TO_FUNCS: Dict[str, Callable] = {
    'paper_section_most_updated_': get_paper_section_most_updated,
    'paper_section_with_table_': get_paper_section_with_table_description,
    'paper_section_with_citations_': get_paper_section_with_citations_description,
    'paper_section_': get_paper_section_description,
}


def get_name_description_iscode(product_field: str) -> Tuple[str, Union[str, Callable]]:
    """
    For the of the given product field, return the name, description, and whether the product is code.
    """
    for section_type, func in SECTION_TYPES_TO_FUNCS.items():
        if product_field.startswith(section_type):
            section_name = product_field[len(section_type):]
            return f'"{section_name}" section of the paper', \
                lambda products: func(products, section_name)

    return PRODUCT_FIELDS_TO_NAME_DESCRIPTION_ISCODE[product_field]
