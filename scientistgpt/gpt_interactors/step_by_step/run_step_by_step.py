from typing import Optional

from scientistgpt.gpt_interactors.step_by_step.goal_and_plan import GoalReviewGPT, PlanReviewGPT
from scientistgpt.gpt_interactors.step_by_step.user_to_student import DirectorToStudent
from scientistgpt.gpt_interactors.step_by_step.write_code import CodeFeedbackGPT
from scientistgpt.gpt_interactors.types import Products


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

    products.analysis_plan = PlanReviewGPT(products=products).initialize_and_run_dialog()

    products.code_and_output = CodeFeedbackGPT(products=products).get_analysis_code()

    products.result_summary = NotImplementedError

    products.implications = NotImplementedError

    return products
