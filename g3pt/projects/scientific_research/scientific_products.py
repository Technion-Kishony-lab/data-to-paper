from dataclasses import dataclass, field, fields
from typing import Optional, List, Dict, Tuple, Union, Callable, Set

from g3pt.base_steps.types import DataFileDescriptions, Products
from g3pt.servers.crossref import CrossrefCitation
from g3pt.base_steps.types import CodeAndOutput
from g3pt.utils.text_utils import dedent_triple_quote_str


@dataclass
class ScientificProducts(Products):
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
        name, description = get_name_and_description(product_field)
        if isinstance(description, str):
            return description.format(getattr(self, product_field))
        else:
            return description(self)

    def get_name(self, product_field: str) -> str:
        """
        Return the name of the given product.
        """
        name, description = get_name_and_description(product_field)
        return name


def get_code_description(products: ScientificProducts) -> str:
    return f'Here is our code:\n\n' \
           f'```python\n{products.code_and_output.code}\n```\n'


def get_code_output_description(products: ScientificProducts) -> str:
    return f'Here is the output of the code (the content of "{products.code_and_output.output_file}"):\n\n' \
           f'```\n{products.code_and_output.output}\n```\n'


def get_code_and_output_description(products: ScientificProducts) -> str:
    return get_code_description(products) + '\n\n' + get_code_output_description(products)


def get_title_and_abstract_description(products: ScientificProducts) -> str:
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


def get_from_paper_sections(products: ScientificProducts, section_name: str) -> str:
    return products.paper_sections[section_name]


def get_from_cited_paper_sections(products: ScientificProducts, section_name: str) -> str:
    return products.cited_paper_sections[section_name][0]


def get_from_paper_sections_with_tables(products: ScientificProducts, section_name: str) -> str:
    return products.paper_sections_with_tables[section_name]


def get_from_most_updated_paper_sections(products: ScientificProducts, section_name: str) -> str:
    for _, func in list(SECTION_TYPES_TO_FUNCS.items())[1:]:  # skip the 'most_updated' section type
        try:
            return func(products, section_name)
        except KeyError:
            pass
    assert False, f'No section named "{section_name}"'


PRODUCT_FIELD_NAMES: List[str] = [field.name for field in fields(Products)]

PRODUCT_FIELDS_TO_NAME_DESCRIPTION: Dict[str, Tuple[str, Union[str, Callable]]] = {
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
    'most_updated_paper_sections': get_from_most_updated_paper_sections,
    'paper_sections_with_tables': get_from_paper_sections_with_tables,
    'cited_paper_sections': get_from_cited_paper_sections,
    'paper_sections': get_from_paper_sections,
}


def get_name_and_description(product_field: str) -> Tuple[str, Union[str, Callable]]:
    """
    For the of the given product field, return the name, description, and whether the product is code.
    """
    for section_type, func in SECTION_TYPES_TO_FUNCS.items():
        if product_field.startswith(section_type):
            section_name = product_field[len(section_type) + 1:]  # +1 for the '_' after the section type
            return f'"{section_name}" section of the paper', \
                lambda products: format_paper_section_description(func(products, section_name), section_name)

    return PRODUCT_FIELDS_TO_NAME_DESCRIPTION[product_field]
