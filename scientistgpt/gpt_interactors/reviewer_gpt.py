from typing import List, Optional


from scientistgpt.utils.text_utils import format_str, print_red
from scientistgpt.conversation import Conversation
from scientistgpt.proceed_retract import FuncAndRetractions

from .converser_gpt import ConverserGPT

MAX_REVIEW_ATTEMPTS = 3


class ReviewerGPT(ConverserGPT):
    """
    Interact with chatgpt to review the results of the analysis.

    Starting with a conversation which ends with a results txt file from the user, ReviewerGPT interacts with chatgpt to
    extract insights from the results or request change to code until it creates satisfactory results that can lead to
    a written paper.

    Interactions with chatgpt include adequate reporting of:
    * empty output file
    * finding unreliable results (not statistically significant)
    * missing important analysis
    * missing figures to support the analysis
    """

    def __init__(self,
                 run_plan: List[FuncAndRetractions] = None,
                 conversation: Optional[Conversation] = None,
                 ):
        super().__init__(run_plan, conversation)
        self._review_iteration = 0

    def _review_plan_last_plan(self, plan: str):
        self._review_iteration += 1
        prompt = format_str("""
        This is the plan for the analysis:
        
        {}
        
        Is this plan satisfactory? (yes/no)
        If no, please specify what needs to be changed.
        If yes, reply yes in one word only.
        """).format(plan)
        self.conversation.append_user_message(prompt)
        response = self.conversation.get_response_from_chatgpt(temperature=0, max_tokens=1)
        return response

    def review_plan(self, analysis_plan: str):
        """
        Review the analysis plan.
        """
        num_review_attempts = 0
        for review_attempt in range(MAX_REVIEW_ATTEMPTS):
            response = self._review_plan_last_plan(analysis_plan)
            if response.lower().__contains__('yes'):
                break
            else:
                prompt = format_str(f"""
                Fix the plan according to the following feedback:
                
                {response}
                
                Return the fixed plan as is, i.e., without mentioning that it's revised.
                you have {MAX_REVIEW_ATTEMPTS - num_review_attempts} attempts left to fix the plan.
                """)
                self.conversation.append_user_message(prompt)
                analysis_plan = self.conversation.get_response_from_chatgpt()
                num_review_attempts += 1
        return analysis_plan