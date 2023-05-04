from typing import Optional

from g3pt.projects.scientific_research.cast import ScientificAgent
from g3pt.projects.scientific_research.add_citations import AddCitationReviewGPT
from g3pt.projects.scientific_research.latex_paper_compilation.assemble_compile_paper import PaperAssemblerCompiler
from g3pt.projects.scientific_research.latex_paper_compilation.get_template import get_paper_section_names
from g3pt.projects.scientific_research.scientific_products import ScientificProducts
from g3pt.projects.scientific_research.steps import GoalReviewGPT, PlanReviewGPT, \
    ResultsInterpretationReviewGPT, PaperSectionReviewGPT, TitleAbstractReviewGPT, PaperSectionWithTablesReviewGPT, \
    ScientificCodeProductsGPT
from g3pt.gpt_interactors.director_converser import DirectorProductGPT
from g3pt.gpt_interactors.types import Products

PAPER_TEMPLATE_FILE: str = 'standard_paper_with_citations.tex'
paper_section_names = get_paper_section_names(PAPER_TEMPLATE_FILE)
SECTIONS_TO_ADD_CITATIONS_TO = ['introduction', 'discussion']
SECTIONS_TO_ADD_TABLES_TO = ['results']


def run_step_by_step(data_file_descriptions, research_goal: Optional[str] = None,
                     data_directory=None, output_directory=None) -> Products:
    products = ScientificProducts()

    # Data file descriptions:
    director_converser = DirectorProductGPT(
        products=products,
        assistant_agent=ScientificAgent.Director,
        user_agent=ScientificAgent.Student,
        conversation_name='with_director',
    )
    products.data_file_descriptions = director_converser.get_product_from_director(
        product_field='data_file_descriptions', returned_product=data_file_descriptions)

    # Goal
    if research_goal is None:
        products.research_goal = GoalReviewGPT(products=products).initialize_and_run_dialog()
    else:
        products.research_goal = director_converser.get_product_from_director(
            product_field='research_goal', returned_product=research_goal)

    # Analysis plan
    products.analysis_plan = PlanReviewGPT(products=products).initialize_and_run_dialog()

    # Code and output
    products.code_and_output = ScientificCodeProductsGPT(products=products).get_analysis_code()

    # Results interpretation
    products.results_summary = ResultsInterpretationReviewGPT(products=products).initialize_and_run_dialog()

    # Paper sections
    title_and_abstract_names = ['title', 'abstract']
    products.paper_sections['title'], products.paper_sections['abstract'] = \
        TitleAbstractReviewGPT(products=products, section_names=title_and_abstract_names).get_sections()

    for section_name in paper_section_names:
        if section_name not in title_and_abstract_names:
            products.paper_sections[section_name] = \
                PaperSectionReviewGPT(products=products, section_name=section_name).get_section()

    # Add citations to relevant paper sections
    for section_name in SECTIONS_TO_ADD_CITATIONS_TO:
        products.cited_paper_sections[section_name] = \
            AddCitationReviewGPT(products=products, section_name=section_name).rewrite_section_with_citations()

    # Add tables to results section
    for section_name in SECTIONS_TO_ADD_TABLES_TO:
        products.paper_sections_with_tables[section_name] = \
            PaperSectionWithTablesReviewGPT(products=products, section_name=section_name).get_section()

    PaperAssemblerCompiler(products=products, output_directory=output_directory).assemble_compile_paper()

    return products
