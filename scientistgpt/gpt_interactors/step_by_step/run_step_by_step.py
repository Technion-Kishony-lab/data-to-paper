from typing import Optional

from scientistgpt.gpt_interactors.paper_writing.get_template import get_paper_section_names
from scientistgpt.gpt_interactors.step_by_step.reviewers import GoalReviewGPT, PlanReviewGPT, \
    ResultsInterpretationReviewGPT
from scientistgpt.gpt_interactors.step_by_step.user_to_student import DirectorToStudent
from scientistgpt.gpt_interactors.step_by_step.write_code import CodeFeedbackGPT
from scientistgpt.gpt_interactors.types import Products


PAPER_TEMPLATE_FILE: str = 'standard_paper_with_citations.tex'


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
    products.paper_sections = get_paper_section_names()

    return products
