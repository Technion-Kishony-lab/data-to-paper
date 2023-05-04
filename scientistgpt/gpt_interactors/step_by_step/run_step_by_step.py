from typing import Optional

from scientistgpt.gpt_interactors.paper_writing.get_template import get_paper_section_names
from scientistgpt.gpt_interactors.step_by_step.add_citations import AddCitationReviewGPT
from scientistgpt.gpt_interactors.step_by_step.reviewers import GoalReviewGPT, PlanReviewGPT, \
    ResultsInterpretationReviewGPT, PaperSectionReviewGPT, TitleAbstractReviewGPT, PaperSectionWithTablesReviewGPT
from scientistgpt.gpt_interactors.step_by_step.user_to_student import DirectorToStudent
from scientistgpt.gpt_interactors.step_by_step.write_code import CodeFeedbackGPT
from scientistgpt.gpt_interactors.step_by_step.latex_paper_compilation.assemble_compile_paper import \
    PaperAssemblerCompiler
from scientistgpt.gpt_interactors.types import Products

PAPER_TEMPLATE_FILE: str = 'standard_paper_with_citations.tex'
paper_section_names = get_paper_section_names(PAPER_TEMPLATE_FILE)
SECTIONS_TO_ADD_CITATIONS_TO = ['introduction', 'discussion']
SECTIONS_TO_ADD_TABLES_TO = ['results']


def run_step_by_step(data_file_descriptions, research_goal: Optional[str] = None,
                     data_directory=None, output_directory=None) -> Products:
    products = Products()

    # Data file descriptions:
    products.data_file_descriptions = DirectorToStudent(products=products).get_product_from_director(
        product_field='data_file_descriptions', returned_product=data_file_descriptions)

    # Goal
    if research_goal is None:
        products.research_goal = GoalReviewGPT(products=products).initialize_and_run_dialog()
    else:
        products.research_goal = DirectorToStudent(products=products).get_product_from_director(
            product_field='research_goal', returned_product=research_goal)

    # Analysis plan
    products.analysis_plan = PlanReviewGPT(products=products).initialize_and_run_dialog()

    # Code and output
    products.code_and_output = CodeFeedbackGPT(products=products).get_analysis_code()

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
