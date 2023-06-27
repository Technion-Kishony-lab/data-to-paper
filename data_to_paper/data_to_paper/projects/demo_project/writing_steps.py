from dataclasses import dataclass
from typing import Tuple

from data_to_paper.base_steps import LatexReviewBackgroundProductsConverser
from data_to_paper.projects.demo_project.cast import DemoAgent
from data_to_paper.projects.demo_project.products import DemoProducts

from data_to_paper.utils import dedent_triple_quote_str


@dataclass
class WriteTitleAndAbstract(LatexReviewBackgroundProductsConverser):
    """
    Base class for the writer of a paper section in latex format.
    """
    conversation_name: str = 'title_and_abstract'
    products: DemoProducts = None
    background_product_fields: Tuple[str, ...] = ('data_file_descriptions', 'research_goal', 'code_and_output')
    product_fields_from_which_response_is_extracted: Tuple[str, ...] = None
    allow_citations_from_step: str = None
    should_remove_citations_from_section: bool = False

    fake_performer_request_for_help: str = \
        'Hi {user_skin_name}, could you please help me {goal_verb} the {pretty_section_names} for my paper?'

    max_reviewing_rounds: int = 1
    goal_noun: str = 'Title and Abstract for a funny math article'
    goal_verb: str = 'write'
    performer: str = 'scientific writer'
    reviewer: str = 'scientific reviewer'
    assistant_agent: DemoAgent = DemoAgent.Performer
    user_agent: DemoAgent = DemoAgent.Writer
    journal_name: str = 'Crazy Math Journal'
    termination_phrase: str = 'This is just great and funny.'

    system_prompt: str = dedent_triple_quote_str("""
        You are a writer.

        You will write a fake funny scientific article for the journal {journal_name}.
        """)

    user_initiation_prompt: str = dedent_triple_quote_str("""
        Based on the material provided above ({actual_background_product_names}), \
        please {goal_verb} only the {goal_noun} for a {journal_name} article.
        Do not write any other parts!

        While making it funny, please make sure to specifically relate to the specific numerical results that we have.

        {latex_instructions}
        """)

    latex_instructions: str = dedent_triple_quote_str("""
        Write in tex format including the \\title{} and \\begin{abstract} ... \\end{abstract} commands, \
        and any math or symbols that needs tex escapes.
        """)

    other_system_prompt: str = dedent_triple_quote_str("""
        You are a reviewer for a writer who is writing a funny scientific-like paper about their results.
        Your job is to provide constructive bullet-point feedback. 
        If you feel that the writing does not need further improvements, you should reply only with:
        "{termination_phrase}".
    """)

    sentence_to_add_at_the_end_of_reviewer_response: str = dedent_triple_quote_str("""\n\n
        Please correct your response according to any points in my feedback that you find relevant and applicable.
        Send back a complete rewrite of the {pretty_section_names}.
        Make sure to send the full corrected {pretty_section_names}, not just the parts that were revised.
    """)

    sentence_to_add_at_the_end_of_performer_response: str = dedent_triple_quote_str("""
        Please provide a bullet-point list of constructive feedback on the above {pretty_section_names} \
        for my paper. Do not provide positive feedback, only provide actionable instructions for improvements in \
        bullet points. 
        In particular, make sure that the section is correctly grounded in the information provided above, \
        yet is written in a funny way.
        If you find any inconsistencies or discrepancies, please mention them explicitly in your feedback.

        You should only provide feedback on the {pretty_section_names}. Do not provide feedback on other sections \
        or other parts of the paper, like tables or Python code, provided above.

        If you don't see any flaws, respond solely with "{termination_phrase}".

        IMPORTANT: You should EITHER provide bullet-point feedback, or respond solely with "{termination_phrase}"; \
        If you chose to provide bullet-point feedback then DO NOT include "{termination_phrase}".
        """)
