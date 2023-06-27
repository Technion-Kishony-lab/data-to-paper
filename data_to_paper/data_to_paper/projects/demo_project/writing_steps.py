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
    goal_noun: str = '{pretty_section_names} section'
    goal_verb: str = 'write'
    performer: str = 'scientific writer'
    reviewer: str = 'scientific reviewer'
    assistant_agent: DemoAgent = DemoAgent.Performer
    user_agent: DemoAgent = DemoAgent.Writer
    section_specific_instructions: str = ''
    section_review_specific_instructions: str = ''
    journal_name: str = 'Nature Communications'

    system_prompt: str = dedent_triple_quote_str("""
        You are a data-scientist with experience writing accurate scientific research papers.

        You will write a scientific article for the journal {journal_name}, following the instructions below:
        1. Write the article section by section: Abstract, Introduction, Results, Discussion, and Methods.
        2. Write every section of the article in scientific language, in `.tex` format.
        3. Write the article in a way that is fully consistent with the scientific results we have.
        """)

    user_initiation_prompt: str = dedent_triple_quote_str("""
        Based on the material provided above ({actual_background_product_names}), \
        please {goal_verb} only the {goal_noun} for a {journal_name} article.
        Do not write any other parts!
        {section_specific_instructions}
        {latex_instructions}
        """)

    latex_instructions: str = dedent_triple_quote_str("""
        Write in tex format including the \\title{} and \\begin{abstract} ... \\end{abstract} commands, \
        and any math or symbols that needs tex escapes.
        """)

    termination_phrase: str = 'I hereby approve the {goal_noun}.'

    other_system_prompt: str = dedent_triple_quote_str("""
        You are a reviewer for a scientist who is writing a scientific paper about their data analysis results.
        Your job is to provide constructive bullet-point feedback.
        We will write each section of the research paper separately. 
        If you feel that the paper section does not need further improvements, you should reply only with:
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
        In particular, make sure that the section is correctly grounded in the information provided above.
        If you find any inconsistencies or discrepancies, please mention them explicitly in your feedback.
        {section_review_specific_instructions}

        You should only provide feedback on the {pretty_section_names}. Do not provide feedback on other sections \
        or other parts of the paper, like tables or Python code, provided above.

        If you don't see any flaws, respond solely with "{termination_phrase}".

        IMPORTANT: You should EITHER provide bullet-point feedback, or respond solely with "{termination_phrase}"; \
        If you chose to provide bullet-point feedback then DO NOT include "{termination_phrase}".
        """)


