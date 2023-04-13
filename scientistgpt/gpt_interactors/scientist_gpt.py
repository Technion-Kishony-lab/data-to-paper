from dataclasses import dataclass, field
from typing import Optional, List

from scientistgpt.utils import dedent_triple_quote_str
from scientistgpt.env import SUPPORTED_PACKAGES
from scientistgpt.conversation.message_designation import RangeMessageDesignation
from scientistgpt.exceptions import ScientistGPTException

from .converser_gpt import CodeWritingGPT
from .debugger_gpt import DebuggerGPT, CodeAndOutput
from .text_extractors import extract_analysis_plan_from_response
from .plan_reviewer_gpt import PlanReviewDialogDualConverserGPT

# structure and terminology:
# analysis plan round (2x):
#   code revisions (different functional versions of the code, 3X):
#       code attempts (different re-trials of versions of the code, 7X per analysis-plan round):
#           debug iterations (recurrent run trials and debugging messages to fix the code, 5X per code attempt)

MAX_ANALYSIS_PLAN_ROUNDS = 2
MAX_PLAN_REVIEW_ROUNDS = 0
MAX_CODE_ATTEMPTS_PER_PLAN = 7
MAX_CODE_REVISIONS = 4
MAX_DEBUG_ITERATIONS_PER_ATTEMPT = 12
MAX_CODING_ATTEMPTS_PER_REVISION = [3, 1, 1, 1]
assert len(MAX_CODING_ATTEMPTS_PER_REVISION) == MAX_CODE_REVISIONS

MAX_REGENERATING_BINARY_RESPONSES = 3


@dataclass
class ScientificProducts:
    """
    Contains the different scientific outcomes of the research.
    These outcomes are gradually populated and refined by the ScientistGPT.

    Allows saving state and rewinding to tagged states
    """
    analysis_plan: Optional[str] = None
    analysis_codes_and_outputs: List[CodeAndOutput] = field(default_factory=list)
    result_summary: Optional[str] = None
    implications: Optional[str] = None
    limitations: Optional[str] = None
    conclusions: Optional[str] = None
    title: Optional[str] = None


@dataclass(frozen=True)
class FailedStepException(ScientistGPTException):
    message: str

    def __str__(self):
        return self.message


@dataclass
class ScientistGPT(CodeWritingGPT):
    """
    Acts as a mentor to a scientist-gpt.
    Create a conversation with chatgpt guiding it through a structured scientific research and analysis of data.

    The user needs to provide:

    data_description: a comprehensive description of the data files available for the project.
                      It is recommended that this description includes a few-line header of each file.

    goal_description: a description of the goal of the analysis.

    ScientistGPT will interact with chatgpt to:
    1. Create analysis plan.
       Send the scientist-gpt to a PlanReviewerGPT to review and enhance the plan.
    2. Implement the plan. Ask the scientist-gpt to write a code to implement the plan.
       Send the scientist-gpt to a debugger to help fix the code.
    3. Review results
    4. Write a scientific paper
    """

    # override the default system_prompt
    system_prompt: str = dedent_triple_quote_str("""
        You are a scientist. I will give you a dataset and a research goal. 
        I will then guide you to perform research in the following steps:
        a. Design a data analysis plan.
        b. Write a data analysis code to perform the analysis plan.
        c. Interpret the results and write a scientific paper about the findings.
        """)

    conversation_name: str = 'ScientistGPT'

    data_description: Optional[str] = None,
    goal_description: Optional[str] = None,

    scientific_products: Optional[ScientificProducts] = field(default_factory=ScientificProducts)

    def add_data_description(self):
        user_prompt = dedent_triple_quote_str("""
            DESCRIPTION OF OUR DATASET.
            We have the following data files:
            {}
            """).format(self.data_description)
        self.conversation_manager.append_user_message(user_prompt, tag='data_description')

        assistant_response = dedent_triple_quote_str("""
            Thank you for the description of the dataset.
            Please also specify the data analysis goal.
            """)
        self.conversation_manager.append_surrogate_message(assistant_response)

    def add_goal_description(self):
        user_prompt = dedent_triple_quote_str("""
            DESCRIPTION OF OUR RESEARCH GOAL.
            {}
            """).format(self.goal_description)
        self.conversation_manager.append_user_message(user_prompt, tag='goal_description')

        assistant_response = dedent_triple_quote_str("""
            Thank you for the goal description.
        """)
        self.conversation_manager.append_surrogate_message(assistant_response, tag='ok_goal_description')

    def devise_analysis_plan(self):
        user_prompt = dedent_triple_quote_str("""
            Suggest a simple data analysis plan to achieve the specified goal.
            """)
        self.scientific_products.analysis_plan = None
        self.scientific_products.analysis_codes_and_outputs = []
        self.conversation_manager.append_user_message(user_prompt, tag='request_analysis_plan')
        self.conversation_manager.get_and_append_assistant_message(tag='analysis_plan')

    def review_analysis_plan(self):
        if MAX_PLAN_REVIEW_ROUNDS == 0:
            return
        self.comment('Asking PlanReviewerGPT for feedback on the plan...', tag='start_reviewing_analysis_plan')

        enhanced_plan_response = PlanReviewDialogDualConverserGPT(
            conversation_name=self.conversation.conversation_name,
            other_conversation_name='PlanReviewer',
            max_rounds=MAX_PLAN_REVIEW_ROUNDS,
        ).initialize_and_run_dialog()

        enhanced_plan = extract_analysis_plan_from_response(enhanced_plan_response)

        # We rewind the conversation to the point where we asked the user to suggest an analysis plan (by giving
        # the same tag), but we replace the original plan with the improved plan that we got from PlanReviewerGPT.
        self.conversation_manager.append_surrogate_message(
            content=dedent_triple_quote_str("""
            Sure, here is a possible data analysis plan:
            {}            
            """).format(enhanced_plan), tag='analysis_plan',
            comment='Rewinding conversation, replacing the original analysis plan with the improved plan.')
        self.scientific_products.analysis_plan = enhanced_plan

    def request_analysis_code(self):
        code_revision = self.number_of_successful_code_revisions
        if code_revision == 0:
            user_prompt = dedent_triple_quote_str("""
                Write a complete short Python code to perform the analysis you suggested.
                Please only use the following packages for your code: {}.
                The output of your code should be a text file named `{}`.
                """).format(SUPPORTED_PACKAGES, self.get_output_filename())
        else:
            user_prompt = dedent_triple_quote_str("""
                Revise the code or any key parameters within it as needed.
                Send me back the complete revised code.
                Do not just point to what needs to be changed, send the full complete code.
                """).format(self.get_output_filename())
        self.conversation_manager.append_user_message(user_prompt, tag=f'request_analysis_code_{code_revision}')

    @property
    def number_of_successful_code_revisions(self):
        return len(self.scientific_products.analysis_codes_and_outputs)

    def get_output_filename(self, after_completion: bool = False, revision_number: Optional[int] = None):
        revision_number = self.number_of_successful_code_revisions if revision_number is None else revision_number
        if after_completion:
            revision_number -= 1
        if revision_number == 0:
            return self.output_filename
        return f'{self.output_filename}_revision{revision_number}'

    def create_and_debug_analysis_code_for_current_revision(self) -> bool:
        """
        Attempt to create and debug the analysis code of the current revision.
        Return True if the code was successfully created and debugged, False otherwise.
        """
        code_revision = self.number_of_successful_code_revisions
        tag = f'analysis_code_revision{code_revision}'
        max_attempts = MAX_CODING_ATTEMPTS_PER_REVISION[code_revision]
        for attempt in range(max_attempts):
            # in each attempt, we are resetting the conversation back to this tag:
            revision_and_attempt = f"Revision {code_revision + 1}/{MAX_CODE_REVISIONS} " \
                                   f"(attempt {attempt + 1}/{max_attempts})"
            self.comment(f'Transfer to DebuggerGPT. {revision_and_attempt}.', tag=tag)

            # we now call the debugger that will try to run and provide feedback in multiple iterations:
            code_and_output = DebuggerGPT(
                max_debug_iterations=MAX_DEBUG_ITERATIONS_PER_ATTEMPT,
                conversation_name=self.conversation.conversation_name,
                gpt_script_filename=f"{self.gpt_script_filename}_revision{code_revision}_attempt{attempt}"
            ).run_debugging()

            if code_and_output is None:
                # debugging failed
                self.comment(f'Debugging failed. {revision_and_attempt}.')
            else:
                # debugging succeeded
                self.scientific_products.analysis_codes_and_outputs.append(code_and_output)
                self.conversation_manager.delete_messages(
                    message_designation=RangeMessageDesignation.from_(start=tag, end=-2),
                    comment='Deleting all debugging correspondence, keeping only the functional code.')
                return True
        return False

    def ask_chatgpt_whether_further_code_revisions_are_needed(self) -> Optional[int]:
        user_prompt = dedent_triple_quote_str("""
            I ran your code. Here is the content of the output file ({}):
            ```
            {}
            ```

            Please choose one of the following options:

            1. I am satisfied with the analysis and the results, I am ready to write a paper about them.

            2. I need to adjust some parameters in the code, or make some other modifications, and then look at 
                the new results again before I can say whether they are interesting enough for a paper.

            Answer with just the number of the option you choose (only type a single character: "1" or "2").            
            """).format(self.get_output_filename(after_completion=True),
                        self.scientific_products.analysis_codes_and_outputs[-1].output)

        self.conversation_manager.append_user_message(
            content=user_prompt,
            tag=f'output_file_content_{self.number_of_successful_code_revisions}')

        response = self.conversation_manager.get_and_append_assistant_message()
        for num_tries in range(MAX_REGENERATING_BINARY_RESPONSES):
            if '1' in response and '2' not in response and len(response) < 5:
                self.comment('ScientistGPT declared it is satisfied with the analysis. Proceeding to result summary.')
                return 1
            elif '2' in response and '1' not in response and len(response) < 5:
                self.comment(f'ScientistGPT declared it needs to revise the code. Starting a new revision '
                             f'({self.number_of_successful_code_revisions + 1}/{MAX_CODE_REVISIONS}).')

                user_prompt = dedent_triple_quote_str("""
                    ok. 
                    Please write a revised version of the code, changing key parameters or anything else needed 
                    to improve the analysis.
                    The output of your code should now be saved to `{}`.
                """).format(self.get_output_filename())
                self.conversation.append_user_message(user_prompt)
                return 2
            else:
                if num_tries < MAX_REGENERATING_BINARY_RESPONSES - 1:
                    response = self.conversation_manager.regenerate_previous_response(
                        comment='ScientistGPT did not choose a valid option. Regenerating response.')
        return None

    def get_gpt_response_to_analysis(self):
        prompt = dedent_triple_quote_str("""
            Fantastic. So, to recap:
            """)

        for code_revision in range(self.number_of_successful_code_revisions):
            prompt += dedent_triple_quote_str("""

            Here is the content of the output file ({}): 
            ```
            {}
            ```

            """).format(self.get_output_filename(revision_number=code_revision),
                        self.scientific_products.analysis_codes_and_outputs[code_revision].output)

        prompt += dedent_triple_quote_str("""            
            Towards writing a scientific paper, you should now:
            1. Describe the results of the analysis.
            2. Describe the implications of the results to the goal of the study. 
            3. Describe the limitations of the analysis.
            """)
        self.conversation_manager.append_user_message(prompt)
        self.conversation_manager.append_surrogate_message('ok, what should I start with?')

        self.conversation_manager.append_user_message(
            'Please start by writing a comprehensive description of the results of the analysis.')
        self.scientific_products.result_summary = self.conversation_manager.get_and_append_assistant_message()

        self.conversation_manager.append_user_message(
            'Perfect. Now, please describe the implications of the results to the goal of the study.')
        self.scientific_products.implications = self.conversation_manager.get_and_append_assistant_message()

        self.conversation_manager.append_user_message(
            'Very good. Now, please describe any limitations of the analysis and results.')
        self.scientific_products.limitations = self.conversation_manager.get_and_append_assistant_message()

    def run_cycles_of_code_and_results(self) -> bool:
        total_code_attempts_for_current_plan = 0
        while True:
            total_code_attempts_for_current_plan += 1
            if total_code_attempts_for_current_plan > MAX_CODE_ATTEMPTS_PER_PLAN:
                return False
            self.request_analysis_code()
            if self.create_and_debug_analysis_code_for_current_revision():
                # code ran successfully
                if self.number_of_successful_code_revisions == MAX_CODE_REVISIONS:
                    return True
                answer = self.ask_chatgpt_whether_further_code_revisions_are_needed()
                if answer == 1:  # chatgpt is satisfied with the analysis
                    return True
                elif answer == 2:  # chatgpt wants to write another code revision
                    continue
                return False
            else:
                # code failed
                if self.number_of_successful_code_revisions == 0:
                    # if we can't even get the first code revision to work, we need a new analysis plan
                    self.comment('Reached max debug attempts for Revision 1. Giving up.')
                    return False
                else:
                    # if we can't get a secondary code revision, we try a new attempt of the first code revision
                    # of the current plan
                    self.scientific_products.analysis_codes_and_outputs.clear()
                    self.comment(
                        f'Reached max debug attempts for Revision {self.number_of_successful_code_revisions + 1}. '
                        f'Trying to go back to revision 1.')
                    continue

    def run_all(self) -> bool:
        self.initialize_conversation_if_needed()
        self.add_data_description()
        self.add_goal_description()
        for analysis_plan_round in range(MAX_ANALYSIS_PLAN_ROUNDS):
            self.devise_analysis_plan()
            self.review_analysis_plan()
            if self.run_cycles_of_code_and_results():
                self.comment('Analysis plan succeeded. Proceeding to result summary.')
                break
            if analysis_plan_round == MAX_ANALYSIS_PLAN_ROUNDS - 1:
                self.comment('Reached max analysis plan rounds. Giving up.')
                return False
        self.get_gpt_response_to_analysis()
