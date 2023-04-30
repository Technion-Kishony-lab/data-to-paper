from typing import Optional

from scientistgpt.gpt_interactors.paper_writing.get_template import get_paper_section_names
from scientistgpt.gpt_interactors.step_by_step.add_citations import AddCitationReviewGPT
from scientistgpt.gpt_interactors.step_by_step.reviewers import GoalReviewGPT, PlanReviewGPT, \
    ResultsInterpretationReviewGPT, PaperSectionReviewGPT, TitleAbstractReviewGPT
from scientistgpt.gpt_interactors.step_by_step.user_to_student import DirectorToStudent
from scientistgpt.gpt_interactors.step_by_step.write_code import CodeFeedbackGPT
from scientistgpt.gpt_interactors.types import Products

PAPER_TEMPLATE_FILE: str = 'standard_paper_with_citations.tex'
paper_section_names = get_paper_section_names(PAPER_TEMPLATE_FILE)
SECTIONS_TO_ADD_CITATIONS_TO = ['introduction', 'discussion']


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
                PaperSectionReviewGPT(products=products, section_names=[section_name]).get_sections()[0]

    # Add citations to relevant paper sections
    section_with_citations, products.bibtex_citations = \
        AddCitationReviewGPT(products=products,
                             sections={section_name: products.paper_sections[section_name] for section_name in
                                       SECTIONS_TO_ADD_CITATIONS_TO}).rewrite_sections_with_citations()
    products.paper_sections.update(section_with_citations)

    return products
