from typing import Optional

from scientistgpt.gpt_interactors.step_by_step.goal_and_plan import GoalReviewGPT, PlanReviewGPT
from scientistgpt.gpt_interactors.step_by_step.write_code import CodeFeedbackGPT
from scientistgpt.gpt_interactors.types import Products


def run_step_by_step(data_file_descriptions, research_goal: Optional[str] = None,
                     data_directory=None, output_directory=None) -> Products:

    products = Products(data_file_descriptions=data_file_descriptions,
                        research_goal=research_goal)
    if research_goal is None:
        products.research_goal = GoalReviewGPT(products).initialize_and_run_dialog()
    products.analysis_plan = PlanReviewGPT(products).initialize_and_run_dialog()

    products.code_and_output = CodeFeedbackGPT(products).get_analysis_code()

    products.result_summary = NotImplementedError

    products.implications = NotImplementedError

    return products
