from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List

from scientistgpt.utils import dedent_triple_quote_str, is_code_in_response
from scientistgpt.env import SUPPORTED_PACKAGES
from scientistgpt.conversation.message_designation import RangeMessageDesignation
from scientistgpt.exceptions import ScientistGPTException
from scientistgpt.cast import Agent

from .converser_gpt import CodeWritingGPT
from .debugger_gpt import DebuggerGPT
from scientistgpt.gpt_interactors.paper_writing import PaperAuthorGPT, FailedCreatingPaper
from .scientific_products import ScientificProducts
from .text_extractors import extract_analysis_plan_from_response
from .plan_reviewer_gpt import PlanReviewDialogDualConverserGPT
from ..utils.text_utils import concat_words_with_commas_and_and

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

    data_file_descriptions: a comprehensive description of the data files available for the project.

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

    list_of_data_files: Optional[List[str]] = None,
    assistant_agent: Agent = Agent.Student
    user_agent: Agent = Agent.Mentor
    goal_description: Optional[str] = None,
    output_directory: Optional[str | Path] = None,
    data_directory: Optional[str | Path] = None,

    scientific_products: Optional[ScientificProducts] = field(default_factory=ScientificProducts)

    def add_data_description(self):
        num_files = len(self.data_file_descriptions)
        user_prompt = "DESCRIPTION OF OUR DATASET.\n\n"
        if num_files == 1:
            user_prompt += "All the data is organized in just one data file:\n\n"
            user_prompt += self.data_file_descriptions[0].pretty_repr()
        else:
            user_prompt += f"We have the following {num_files} data files:\n"
            for file_number, data_file_description in enumerate(self.data_file_descriptions):
                user_prompt += f"\n({file_number + 1}) " + data_file_description.pretty_repr()

        self.apply_append_user_message(user_prompt, tag='data_description')

        assistant_response = dedent_triple_quote_str("""
            Thank you for the description of the dataset.
            Please also specify the data analysis goal.
            """)
        self.apply_append_surrogate_message(assistant_response)
        # add the data description to the scientific products
        self.scientific_products.data_description = user_prompt

    def add_goal_description(self):
        user_prompt = dedent_triple_quote_str("""
            DESCRIPTION OF OUR RESEARCH GOAL.
            {}
            """).format(self.goal_description)
        self.apply_append_user_message(user_prompt, tag='goal_description')

        assistant_response = dedent_triple_quote_str("""
            Thank you for the goal description.
        """)
        self.apply_append_surrogate_message(assistant_response, tag='ok_goal_description')
        # add the goal description to the scientific products
        self.scientific_products.goal_description = self.goal_description

    def devise_analysis_plan(self):
        user_prompt = dedent_triple_quote_str("""
            Suggest a simple data analysis plan to achieve the specified goal.
            """)
        self.scientific_products.analysis_plan = None
        self.scientific_products.analysis_codes_and_outputs = []
        self.apply_append_user_message(user_prompt, tag='request_analysis_plan')
        self.apply_get_and_append_assistant_message(tag='analysis_plan')
        self.scientific_products.analysis_plan = extract_analysis_plan_from_response(
            self.conversation_manager.conversation.get_last_response())

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
        self.apply_append_surrogate_message(
            content=dedent_triple_quote_str("""
            Sure, here is a possible data analysis plan:
            {}
            """).format(enhanced_plan), tag='analysis_plan',
            comment='Rewinding conversation, replacing the original analysis plan with the improved plan.')
        self.scientific_products.analysis_plan = enhanced_plan

    @property
    def _request_code_tag(self):
        return f'code_revision_{self.number_of_successful_code_revisions}'

    def request_analysis_code(self):
        if self.number_of_successful_code_revisions == 0:
            user_prompt = dedent_triple_quote_str("""
                Write a complete short Python code to perform the analysis you suggested.
                If needed, you can use the following packages in your code: {}.
                The output of your code should be a text file named `{}`.
                The results should be in a summarized form, do not plot anything to screen or file.
                """).format(concat_words_with_commas_and_and(SUPPORTED_PACKAGES, '`'), self.get_output_filename())
        else:
            user_prompt = dedent_triple_quote_str("""
                Revise the code, or just change any key parameters (like thresholds, etc) within the code as needed.
                The output of your new code should be a text file named `{}`.
                Send me back the complete revised code.
                Do not just point to what needs to be changed, send the full complete code.
                """).format(self.get_output_filename())
        self.apply_append_user_message(user_prompt, tag=self._request_code_tag)

    @property
    def number_of_successful_code_revisions(self):
        return len(self.scientific_products.analysis_codes_and_outputs)

    def get_output_filename(self, after_completion: bool = False, revision_number: Optional[int] = None):
        revision_number = self.number_of_successful_code_revisions if revision_number is None else revision_number
        if after_completion:
            revision_number -= 1
        if revision_number == 0:
            return self.output_filename
        return self.output_filename.replace('.', f'_revision_{revision_number}.')

    def create_and_debug_analysis_code_for_current_revision(self) -> bool:
        """
        Attempt to create and debug the analysis code of the current revision.
        Return True if the code was successfully created and debugged, False otherwise.
        """
        code_revision = self.number_of_successful_code_revisions
        tag = self._request_code_tag + '_debugging'
        max_attempts = MAX_CODING_ATTEMPTS_PER_REVISION[code_revision]
        for attempt in range(max_attempts):
            # in each attempt, we are resetting the conversation back to this tag:
            revision_and_attempt = f"Revision {code_revision + 1}/{MAX_CODE_REVISIONS} " \
                                   f"(attempt {attempt + 1}/{max_attempts})"
            self.comment(f'Transfer to DebuggerGPT. {revision_and_attempt}.', tag=tag)

            # we now call the debugger that will try to run and provide feedback in multiple iterations:
            code_and_output = DebuggerGPT(
                output_filename=self.get_output_filename(),
                data_file_descriptions=self.data_file_descriptions,
                max_debug_iterations=MAX_DEBUG_ITERATIONS_PER_ATTEMPT,
                conversation_name=self.conversation.conversation_name,
                gpt_script_filename=f"{self.gpt_script_filename}_revision{code_revision}_attempt{attempt}"
            ).run_debugging()

            if code_and_output is None:
                # debugging failed
                self.comment(f'Debugging failed. {revision_and_attempt}.')
            else:
                # debugging succeeded. we now forge the conversation as if chatgpt immediately sent the correct code:
                self.conversation_manager.delete_messages(
                    message_designation=RangeMessageDesignation.from_(start=tag, end=-1),
                    comment='Deleting all debugging correspondence.')
                assert self.conversation[-1].tag == self._request_code_tag

                self.apply_append_surrogate_message(
                    content=dedent_triple_quote_str("""
                    Here is the code to perform the analysis:
                    ```python
                    {}
                    ```
                    """).format(code_and_output.code),
                    comment='Adding the debugged code as if it was the original response.',
                    is_code=True,
                )
                # the conversation is now at a point as if chatgpt immediately sent the correct code in response to
                # the request for code. However, the code is now given without any explanation.
                # We therefore ask chatgpt to explain the code:

                self.apply_append_user_message(
                    content=dedent_triple_quote_str("""
                    Please explain what your code does (Do not make new comments in the code itself, 
                    just explain what the code does).

                    Also explain what does the code writes into the {} file, and what do we expect to see in that file.
                    """).format(self.get_output_filename()),
                )
                self.apply_get_and_append_assistant_message()
                self.scientific_products.analysis_codes_and_outputs.append(code_and_output)
                return True
        return False

    def ask_chatgpt_whether_further_code_revisions_are_needed(self) -> Optional[int]:
        user_prompt = dedent_triple_quote_str("""
            I ran your code. Here is the content of the output file ({}):
            ```
            {}
            ```

            Please choose one of the following options:

            a. I am satisfied with the analysis and the results, I am ready to write a paper about them.

            b. I need to adjust some parameters in the code, or make some other modifications, and then look at 
                the new results again before I can say whether they are interesting enough for a paper.

            Answer with just the number of the option you choose (only type a single character: "a" or "b").
            Under any circumstances, answer with just one character matching the option you choose, nothing else.            
            """).format(self.get_output_filename(after_completion=True),
                        self.scientific_products.analysis_codes_and_outputs[-1].output)

        self.apply_append_user_message(
            content=user_prompt,
            tag=f'output_file_content_{self.number_of_successful_code_revisions}')

        response = self.apply_get_and_append_assistant_message()
        for num_tries in range(MAX_REGENERATING_BINARY_RESPONSES):
            if 'a' in response and 'b' not in response and len(response) < 5:
                self.comment('ScientistGPT declared it is satisfied with the analysis. Proceeding to result summary.')
                return 1
            elif 'b' in response and 'a' not in response and len(response) < 5:
                self.comment(f'ScientistGPT declared it needs to revise the code. Starting a new revision '
                             f'({self.number_of_successful_code_revisions + 1}/{MAX_CODE_REVISIONS}).')
                return 2
            elif is_code_in_response(response):
                # the scientist sent code, so we assume it wants to change the code (choosing "2")
                response = self.conversation_manager.replace_last_response(
                    content='b',
                    comment='ChatGPT sent code instead of "a"/"b". We assume it wants to change the code ("b").')
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
        self.apply_append_user_message(prompt)
        self.apply_append_surrogate_message('ok, what should I start with?')

        self.apply_append_user_message(
            'Please start by writing a comprehensive description of the results of the analysis. '
            'in addition finish with a short summary of the code packages and other tools used for the analysis.')
        self.scientific_products.result_summary = self.apply_get_and_append_assistant_message(tag='result_summary')

        self.apply_append_user_message(
            'Perfect. Now, please describe the implications of the results to the goal of the study.')
        self.scientific_products.implications = self.apply_get_and_append_assistant_message(tag='implications')

        self.apply_append_user_message('Very good. Now, please describe any limitations of the analysis and results.')
        self.scientific_products.limitations = self.apply_get_and_append_assistant_message(tag='limitations')

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
                    self.comment(
                        f'Reached max debug attempts for Revision {self.number_of_successful_code_revisions + 1}. '
                        f'Trying to go back to revision 1.')
                    self.scientific_products.analysis_codes_and_outputs.clear()
                    continue

    def call_paper_author_to_write_and_compile_paper(self) -> bool:
        self.comment('Starting the paper writing process.')
        paper_author = PaperAuthorGPT(scientific_products=self.scientific_products,
                                      output_directory=self.output_directory)
        try:
            paper_author.write_paper()
            return True
        except FailedCreatingPaper:
            return False

    def run_all(self) -> bool:
        self.initialize_conversation_if_needed()
        self.add_data_description()
        self.add_goal_description()
        for analysis_plan_round in range(MAX_ANALYSIS_PLAN_ROUNDS):
            if analysis_plan_round > 0:
                self.comment(f'Rethinking analysis plan (round {analysis_plan_round + 1}/{MAX_ANALYSIS_PLAN_ROUNDS}).')
            self.devise_analysis_plan()
            self.review_analysis_plan()
            if not self.run_cycles_of_code_and_results():
                continue  # try a new analysis plan
            self.get_gpt_response_to_analysis()
            if not self.call_paper_author_to_write_and_compile_paper():
                continue  # try a new analysis plan
            break
        else:
            self.comment('Reached max analysis plan rounds. Manuscript NOT created. Giving up.')
            return False
        self.comment('Manuscript created successfully.')
        return True
