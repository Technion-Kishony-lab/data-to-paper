from dataclasses import dataclass, field, fields
from typing import Optional, List, Dict, Tuple, Union, Callable, Set

from scientistgpt.projects.scientific_research.scientific_stage import ScientificStage
from scientistgpt.run_gpt_code.types import CodeAndOutput
from scientistgpt.utils.text_utils import dedent_triple_quote_str, NiceList
from scientistgpt.base_steps.types import DataFileDescriptions, Products
from scientistgpt.servers.crossref import CrossrefCitation


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
    tabled_paper_sections: Dict[str, str] = field(default_factory=dict)

    def get_description(self, product_field: str) -> str:
        """
        Return the description of the given product.
        """
        name, stage, description = get_name_stage_and_description(product_field)
        if isinstance(description, str):
            return description.format(getattr(self, product_field))
        else:
            return description(self)

    def get_name(self, product_field: str) -> str:
        """
        Return the name of the given product.
        """
        name, stage, description = get_name_stage_and_description(product_field)
        return name

    def get_stage(self, product_field: str) -> ScientificStage:
        """
        Return the stage of the given product.
        """
        name, stage, description = get_name_stage_and_description(product_field)
        return stage


def get_code_description(products: ScientificProducts) -> str:
    return f'Here is our code:\n\n' \
           f'```python\n{products.code_and_output.code}\n```\n'


def get_code_output_description(products: ScientificProducts) -> str:
    return f'Here is the output of the code (the content of "{products.code_and_output.output_file}"):\n\n' \
           f'```\n{products.code_and_output.output}\n```\n'


def get_code_and_output_description(products: ScientificProducts) -> str:
    return get_code_description(products) + '\n\n\n' + get_code_output_description(products)


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
    return products.tabled_paper_sections[section_name]


def get_from_most_updated_paper_sections(products: ScientificProducts, section_name: str) -> str:
    for _, (func, stage) in list(SECTION_TYPES_TO_FUNCS_AND_STAGES.items())[1:]:  # skip the 'most_updated' section type
        try:
            return func(products, section_name)
        except KeyError:
            pass
    assert False, f'No section named "{section_name}"'


def get_paper(paper_sections: Dict[str, str]) -> str:
    """
    Compose the paper from the different paper sections.
    product_field can be one of the following:
    paper_sections
    cited_paper_sections
    tabled_paper_sections
    """
    paper = ''
    for section_name, section_content in paper_sections.items():
        paper += f"``{section_name}``\n\n{section_content}\n\n\n"
    return paper


def get_citations(products: ScientificProducts) -> NiceList[CrossrefCitation]:
    """
    Return the citations of the paper.
    """
    citations = set()
    for section_content, section_citations in products.cited_paper_sections.values():
        citations.update(section_citations)
    return NiceList(citations, separator='\n\n', last_separator=None)


def get_cited_sections_and_citations(products: ScientificProducts) -> str:
    """
    Return the cited sections and the citation list.
    """
    citations = get_citations(products)
    cited_sections = get_paper(
        {section_name: section_content for section_name, (section_content, _) in products.cited_paper_sections.items()})
    return f'{cited_sections}\n\n\n``Citations``\n\n{citations}'


PRODUCT_FIELD_NAMES: List[str] = [field.name for field in fields(Products)]

PRODUCT_FIELDS_TO_NAME_STAGE_DESCRIPTION: Dict[str, Tuple[str, Optional[ScientificStage], Union[str, Callable]]] = {
    'data_file_descriptions': ('Dataset', ScientificStage.DATA, 'DESCRIPTION OF DATASET\n\nWe have the following {}'),
    'research_goal': ('Research Goal', ScientificStage.GOAL, 'DESCRIPTION OF OUR RESEARCH GOAL.\n\n{}'),
    'analysis_plan': ('Data Analysis Plan', ScientificStage.PLAN, 'Here is our data analysis plan:\n\n{}'),
    'code': ('code', ScientificStage.CODE, get_code_description),
    'code_output': ('Output of the Code', ScientificStage.CODE, get_code_output_description),
    'code_and_output': ('Code and Output', ScientificStage.CODE, get_code_and_output_description),
    'results_summary': ('Results Summary', ScientificStage.INTERPRETATION, 'Here is a summary of our results:\n\n{}'),
    'title_and_abstract': ('Title and Abstract', ScientificStage.WRITING, get_title_and_abstract_description),
    'paper_sections':
        ('Paper Sections', ScientificStage.WRITING, lambda products: get_paper(getattr(products, 'paper_sections'))),
    'cited_paper_sections':
        ('Cited Paper Sections and Citations', ScientificStage.CITATIONS, get_cited_sections_and_citations),
    'tabled_paper_sections':
        ('Paper Sections with Tables', ScientificStage.TABLES,
         lambda products: get_paper(getattr(products, 'tabled_paper_sections'))),
}

SECTION_TYPES_TO_FUNCS_AND_STAGES: Dict[str, Tuple[Callable, Optional[ScientificStage]]] = {
    'most_updated_paper_sections:': (get_from_most_updated_paper_sections, None),
    'paper_sections_with_tables:': (get_from_paper_sections_with_tables, ScientificStage.TABLES),
    'cited_paper_sections:': (get_from_cited_paper_sections, ScientificStage.CITATIONS),
    'paper_sections:': (get_from_paper_sections, ScientificStage.WRITING),
}


def get_name_stage_and_description(product_field: str) -> Tuple[str, ScientificStage, Union[str, Callable]]:
    """
    For the of the given product field, return the name, description, and whether the product is code.
    """
    for section_type, (func, stage) in SECTION_TYPES_TO_FUNCS_AND_STAGES.items():
        if product_field.startswith(section_type):
            section_name = product_field[len(section_type):]
            return f'{section_name.title()} section of the paper', \
                stage, \
                lambda products: format_paper_section_description(func(products, section_name), section_name)

    return PRODUCT_FIELDS_TO_NAME_STAGE_DESCRIPTION[product_field]
