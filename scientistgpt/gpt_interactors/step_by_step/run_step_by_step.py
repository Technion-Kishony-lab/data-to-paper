from typing import Optional

from scientistgpt.gpt_interactors.step_by_step.goal_and_plan import GoalReviewGPT, PlanReviewGPT, CodeFeedbackGPT
from scientistgpt.gpt_interactors.types import Products


def run_step_by_step(data_files, research_goal: Optional[str] = None)
    products = Products(data_files=data_files, research_goal=research_goal)
    if research_goal is None:
        products.goal = GoalReviewGPT(products).initialize_and_run_dialog()
    products.plan = PlanReviewGPT(products).initialize_and_run_dialog()

    products.analysis_codes_and_outputs[0] = CodeFeedbackGPT(products)._run_debugger()

    for revision in range(1, 3):
        code = CodeRevisionReviewGPT(products).run()
        if code is None:
            break
        products.code[revision] = code
    products.result_summary = ResultReviewGPT(products).run()

    products.paper_sections = ResultReviewGPT(products).run()

