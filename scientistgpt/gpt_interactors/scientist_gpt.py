import copy
from dataclasses import dataclass
from typing import Optional, List, Callable

from scientistgpt.proceed_retract import FuncAndRetractions, ExecutionPlan, ProceedRetract
from scientistgpt.exceptions import FailedDebuggingException
from scientistgpt.utils.text_utils import dedent_triple_quote_str, print_red
from scientistgpt.env import SUPPORTED_PACKAGES
from .plan_reviewer_gpt import PlanReviewerGPT

from .debugger_gpt import DebuggerGPT
from .converser_gpt import ConverserGPT, CodeWritingGPT
from ..conversation.converation_manager import ConversationManager


MAX_ANALYSIS_REVISIONS = 2

# NOTE: For the text of gpt prompt, we use the triple-quote notation because it elegantly takes care of newlines
#       and can be integrated within the class functions.
#       Any preceding spaces are removed with dedent_triple_quote_str().
#       Note though that this notation does not work with f-string formatting especially when the dynamically
#       added text includes multiple lines.
#       We therefore use instead the triple-quote with the .format() notation to get a dynamic, yet structured and
#       readable, multi-line text.


@dataclass
class ScientificMentorGPT(CodeWritingGPT, ProceedRetract):
    """
    Acts as a mentor to a scientist-gpt.
    Create a conversation with chatgpt provoking a structured scientific research involving analysis of data.

    The user needs to provide:

    data_description: a comprehensive description of the data files available for the project.
                      It is recommended that this description includes a few-line header of each file.

    goal_description: a description of the goal of the analysis.

    ScientificMentorGPT will interact with chatgpt to:
    1. Create analysis plan.
       Send the scientist-gpt to a PlanReviewerGPT to review and enhance the plan.
    2. Implement the plan. Ask the scientist-gpt to write a code to implement the plan.
       Send the scientist-gpt to a CodeReviewerGPT to review and enhance the code.
    3. Review results
    4. Write a scientific paper
    """

    # override the default system_prompt
    system_prompt = dedent_triple_quote_str("""
        You are a scientist. You are given a dataset and a goal. You will need to:
        1. design a data analysis plan.
        2. write an efficient short code to perform the analysis plan.
        3. interpret the results and write a summary of the findings.
        """)

    # override the default conversation_name
    conversation_name = 'ScientificMentorGPT'

    data_description: Optional[str] = None,
    goal_description: Optional[str] = None,
    message_callback: Optional[Callable] = None

    analysis_plan_reviewing_cycles: int = 0  # max number of cycles of plan reviewing. 0 means no plan review.

    def __post_init__(self):
        CodeWritingGPT.__post_init__(self)
        ProceedRetract.__post_init__(self)
        self._run_code_attempt = 0
        self._conversation_manager: ConversationManager = ConversationManager(conversation_name=self.conversation_name)
        self.analysis_plan: Optional[str] = None
        self.results_summary: Optional[str] = None
        self.output_file_content: Optional[str] = None
        self.pre_paper_conversation = None

    def add_data_description(self):
        prompt = dedent_triple_quote_str("""
            We have the following data files:

            {}
            """).format(self.data_description)
        self.conversation_manager.append_user_message(prompt, 'data_description')

        response = dedent_triple_quote_str("""
            Thank you for the description of the dataset.
            Please also specify the data analysis goal.
            """)
        self.conversation_manager.append_provided_assistant_message(response)

    def add_goal_description(self):
        prompt = self.goal_description
        self.conversation_manager.append_user_message(prompt, tag='goal_description')
        self.conversation_manager.append_provided_assistant_message('Thank you for the goal description.',
                                                                    tag='ok_goal_description')

    def request_analysis_plan(self):
        prompt = dedent_triple_quote_str("""
            Suggest a data analysis plan to achieve the specified goal.
            """)
        self.conversation_manager.append_user_message(prompt, 'request_analysis_plan')
        self.conversation_manager.get_and_append_assistant_message(tag='analysis_plan')

    def review_analysis_plan(self):
        if self.analysis_plan_reviewing_cycles == 0:
            return
        self.conversation_manager.append_commenter_message(
            'Asking PlanReviewerGPT for feedback on the analysis plan...')
        enhanced_plan = PlanReviewerGPT(
            other_conversation_name=self.conversation.conversation_name,
            max_review_cycles=self.analysis_plan_reviewing_cycles,
        ).review_plan()

        # by giving the same tag. we trim the conversation back, as if the improved plan was the original plan:
        self.conversation_manager.append_provided_assistant_message(enhanced_plan, tag='analysis_plan')

    def request_analysis_code(self):
        prompt = dedent_triple_quote_str("""
            Write a complete Python code to perform the analysis you suggested.
            Use only the packages: {} to perform the analysis.
            The output of your code should be a text file named `{}`.
            Any plots produced should be saved as image files and should not display to screen.
            """).format(SUPPORTED_PACKAGES, self.output_filename)
        self.conversation.append_user_message(prompt)

    def run_gpt_code_and_add_output_to_conversation(self):
        print_red('Transfer control to DebuggerGPT to debug and get a functional code ...')
        self._run_code_attempt += 1
        debugger = DebuggerGPT(conversation=copy.deepcopy(self.conversation),
                               script_file=f"{GPT_SCRIPT_FILENAME}_{self._run_code_attempt}",
                               new_file_for_each_try=True)
        result = debugger.debug_and_run_code()
        self.output_file_content = result
        # self.conversation = debugger.conversation
        print_red("Code ran successfully! Let's see what chatgpt think of the results ...")

        prompt = dedent_triple_quote_str("""
            I ran your code. Here is the content of the output file ({}):
            ```
            {}
            ```
            
            You are obliged to choose one of the following options:
            1. I am satisfied with the analysis and the results, I am ready to write a paper about them.
            2. I need to write additional code the code and try again before writing a paper.
            
            Answer with the number of the option you choose only, i.e "1" or "2".
            """).format(self.OUTPUT_FILENAME, result)
        self.conversation.append_user_message(prompt)

    def get_gpt_improvement_to_analysis(self):
        analysis_revises = 0
        while analysis_revises < MAX_ANALYSIS_REVISIONS:
            result = self.conversation.get_response_from_chatgpt()
            if result == '1':
                print_red('ChatGPT declared "I am satisfied with the analysis and the results, I am ready to write a paper about them."')
                break

            if result == '2':
                print_red(
                    'ChatGPT declared "I need to write additional code the code and try again before writing a paper."')
                prompt = dedent_triple_quote_str("""
                Write additional code to improve the analysis and try again. Append any additional results to the output file.
                """)
                self.conversation.append_user_message(prompt)
                self.conversation.get_response_from_chatgpt()
                self.run_gpt_code_and_add_output_to_conversation()
            analysis_revises += 1

    def get_gpt_response_to_analysis(self):
        # ask chatgpt to summarize the results
        prompt = dedent_triple_quote_str("""
            The results file contains the following content:
            ```
            {}
            ```
            Summarize the results of the analysis. Include comments about plots you generated.
            """).format(self.output_file_content)
        self.conversation.append_user_message(prompt)
        self.results_summary = self.conversation.get_response_from_chatgpt()

    def prepare_pre_paper_conversation(self):
        print_red('Preparing the pre-paper conversation ...')
        paper_conversation = Conversation()
        paper_conversation.append_message(role=Role.SYSTEM, message='You are a helpful scientist that able to write scientific papers.')
        paper_conversation.append_user_message('This is the data description\n\n' + self.data_description)
        paper_conversation.append_assistant_message('acknowledged')
        paper_conversation.append_user_message('This is the research goal description\n\n' + self.goal_description)
        paper_conversation.append_assistant_message('acknowledged')
        paper_conversation.append_user_message('This is the analysis plan description\n\n' + self.analysis_plan)
        paper_conversation.append_assistant_message('acknowledged')
        paper_conversation.append_user_message('This is the analysis results description\n\n' + self.results_summary)
        paper_conversation.append_assistant_message('acknowledged')
        print_red('Pre-paper conversation is ready! Let\'s write the paper ...')
        self.pre_paper_conversation = paper_conversation


    def write_paper(self):
        prompt = dedent_triple_quote_str("""
        Write paper - write abstract, introduction, methods, results, discussion and acknowledgments.
        Use markdown to format the paper.
        In addition you are required to state where to enter the figure of you created during the analysis by using
        FIGURE@#@ name_of_figure @#@ where name_of_figure is the name of the figure you want to enter.
        Add references to the paper if applicable.
        """)
        self.pre_paper_conversation.append_user_message(prompt)
        self.pre_paper_conversation.get_response_from_chatgpt()
        paper = self.pre_paper_conversation.get_last_response()
        self.conversation.append_user_message(prompt)
        self.conversation.append_assistant_message(paper)
        # save the paper to file
        with open('paper.txt', 'w') as f:
            f.write(paper)


upon_code_failure = [1, 1, 2, 1, 1]
# This means that if the code failed despite debugging attempts (as defined by DebuggerGPT),
# we go back 1 step (to request_analysis_code). If it fails again, we go back again 1 step. If it then fails for
# the third time, we go back 2 steps (to request_analysis_plan, thus revising the whole plan).
# We then try again the same process on the new plan (going back 1 step for two failures [1, 1]).
# If it still fails, we end and raise an exception.

ScientistGPT_EXECUTION_PLAN: ExecutionPlan = [
    FuncAndRetractions('initialize_conversation', (), []),
    FuncAndRetractions('add_data_description', (), []),
    FuncAndRetractions('add_goal_description', (), []),
    FuncAndRetractions('request_analysis_plan', (), []),
    FuncAndRetractions('review_analysis_plan', (), []),
    FuncAndRetractions('request_analysis_code', (), []),
    FuncAndRetractions('run_gpt_code_and_add_output_to_conversation', FailedDebuggingException, upon_code_failure),
    FuncAndRetractions('get_gpt_response_to_analysis', (), []),
    FuncAndRetractions('prepare_pre_paper_conversation', (), []),
    FuncAndRetractions('write_paper', (), []),
]
