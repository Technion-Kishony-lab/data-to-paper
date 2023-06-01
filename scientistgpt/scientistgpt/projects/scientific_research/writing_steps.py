from dataclasses import dataclass, field
from typing import Tuple

from scientistgpt.base_steps import BaseLatexProductsReviewGPT
from scientistgpt.projects.scientific_research.cast import ScientificAgent
from scientistgpt.servers.openai_models import ModelEngine
from scientistgpt.utils import dedent_triple_quote_str
from scientistgpt.utils.nice_list import nicely_join


@dataclass
class SectionWriterReviewGPT(BaseLatexProductsReviewGPT):
    """
    Base class for the writer of a paper section in latex format.
    """
    background_product_fields: Tuple[str] = ('data_file_descriptions', 'research_goal',
                                             'codes:data_analysis', 'tables_and_numeric_values', 'results_summary',
                                             'title_and_abstract')

    fake_performer_request_for_help: str = \
        'Hi {user_skin_name}, could you please help me {goal_verb} the {pretty_section_names} for my paper?'

    max_reviewing_rounds: int = 1
    goal_noun: str = '{pretty_section_names} section of the paper'
    conversation_name: str = None
    goal_verb: str = 'write'
    performer: str = 'scientific writer'
    reviewer: str = 'scientific reviewer'
    assistant_agent: ScientificAgent = ScientificAgent.Performer
    user_agent: ScientificAgent = ScientificAgent.Writer
    section_specific_instructions: str = ''
    section_review_specific_instructions: str = ''

    system_prompt: str = dedent_triple_quote_str("""
        You are a data-scientist with experience writing accurate scientific research papers.

        You should:
        1. Write every section of the paper in scientific language, in `.tex` format.
        2. Write the paper section by section.
        3. Write the paper in a way that is fully consistent with the scientific products we have.
        4. Write the text without adding any citations (we will only add citations in a later stage).
        """)

    user_initiation_prompt: str = dedent_triple_quote_str("""
        Based on the material provided above ({actual_background_product_names}), \
        please {goal_verb} only the {pretty_section_names} of a scientific paper.
        Do not write any other parts!
        {section_specific_instructions}
        {latex_instructions}
        """)

    latex_instructions: str = dedent_triple_quote_str("""
        Write in tex format including the \\section{} command, and any math or symbols that needs tex escapes.
        """)

    termination_phrase: str = 'I hereby approve the paper section'

    other_system_prompt: str = dedent_triple_quote_str("""
        You are a reviewer for a scientist who is writing a scientific paper about their data analysis results.
        Your job is to provide constructive bullet-point feedback in repeated cycles \
        of improvements and feedback.
        We will write each section of the research paper separately. 
        When you feel that the paper section is well-written and accurate, you should explicitly say:
        "{termination_phrase}".
        If you feel that my initial writing is already good enough, it is perfectly fine \
        to respond immediately with the above phrase ("{termination_phrase}"), \
        without requesting any improvement cycles.
    """)

    sentence_to_add_at_the_end_of_reviewer_response: str = dedent_triple_quote_str("""
        Please correct your response according to my feedback and send back a complete rewrite \
        of the {pretty_section_names}.
        Make sure to send the full corrected {pretty_section_names}, not just the parts that were revised.
    """)
    sentence_to_add_at_the_end_of_performer_response: str = dedent_triple_quote_str("""
        Please provide constructive feedback on the above {pretty_section_names} for my paper.
        Either reply with a bullet-point list of feedback points, or, if you feel that the section is already \
        good enough, respond with "{termination_phrase}" only. 
        
        Do not summarize the content of the section in your feedback, only provide feedback in bullet points.
        
        {section_review_specific_instructions}
        
        In addition, make sure that the section is grounded in the information provided above and is consistent with it.
        If you find any inconsistencies or discrepancies, please mention them explicitly in your feedback.
        """)

    def __post_init__(self):
        self.conversation_name = self.conversation_name or nicely_join(self.section_names, separator='_')
        super().__post_init__()


@dataclass
class TitleAbstractSectionWriterReviewGPT(SectionWriterReviewGPT):
    max_reviewing_rounds: int = 2
    latex_instructions: str = dedent_triple_quote_str("""
        Write in tex format including the \\title{} and \\begin{abstract} ... \\end{abstract} commands, \
        and any math or symbols that needs tex escapes.
        """)


@dataclass
class IntroductionSectionWriterReviewGPT(SectionWriterReviewGPT):
    background_product_fields: Tuple[str] = ('data_file_descriptions', 'research_goal', 'title_and_abstract',
                                             'most_updated_paper_sections:methods',
                                             'most_updated_paper_sections:results')
    max_reviewing_rounds: int = 1
    section_specific_instructions: str = dedent_triple_quote_str("""
        The introduction should introduce the topic of the paper.
        It should then give a general overview and some background on the topic of the paper.
        It should then explain the research goal of the paper and what is the main contribution of the paper.
        The introduction should be interesting and pique your reader’s interest.
        """)


@dataclass
class MethodsSectionWriterReviewGPT(SectionWriterReviewGPT):
    background_product_fields: Tuple[str] = ('data_file_descriptions', 'research_goal', 'codes:data_preprocessing',
                                             'codes:data_analysis', 'title_and_abstract')
    max_reviewing_rounds: int = 1
    model_engine: ModelEngine = field(default_factory=lambda: ModelEngine.GPT4)
    section_specific_instructions: str = dedent_triple_quote_str("""
        Make sure that you are only referring to analysis steps that are explicitly performed by the \
        data preprocessing code and data analysis code (see Python blocks above).

        Focus on the methods that were used to achieve the research goal.
        """)

    section_review_specific_instructions: str = dedent_triple_quote_str("""\n
        Specifically, pay attention to:
        * Over-specific description of tools, like specifying exact software or package versions used in the analysis.
        * Description of analysis steps that were not performed by the analysis Python codes \
        (provided above), like certain data cleaning processes.
        * References to variables and data files that were not used in the analysis.
        """)


@dataclass
class ReferringTablesSectionWriterReviewGPT(SectionWriterReviewGPT):
    user_agent: ScientificAgent = ScientificAgent.TableExpert
    background_product_fields: Tuple[str] = ('most_updated_paper_sections:{methods}',
                                             'title_and_abstract', 'tables_and_numeric_values')
    max_reviewing_rounds: int = 1
    section_specific_instructions: str = dedent_triple_quote_str("""\n
        As you write the results, \
        refer to the Tables by their labels and explain their content, but do not add the tables themselves \
        (I will add the tables later manually).

        You can also extract and use any of the key Numerical Values provided above that you think are \
        scientifically meaningful. Note though that, unlike the Tables, these Numerical Values are not going to be \
        added as a part of the paper, so you should explicitly mention any important values as an integral part of \
        the text.

        Make sure that you are only mentioning details that are explicitly found within the Tables and Numerical Values.
        """)
    section_review_specific_instructions: str = dedent_triple_quote_str("""
        Specifically, pay attention to:
        whether the {goal_noun} contains only information that is explicitly extracted from the \
        Tables and Numerical Values provided above. \
        
        Compare the numbers in the {goal_noun} with the numbers in the Tables and Numerical Values and explicitly \
        mention any discrepancies that need to be fixed.
        
        Do not suggest changes to the {goal_noun} that may require data not available in the the \
        Tables and Numerical Values.
        """)


@dataclass
class DiscussionSectionWriterReviewGPT(SectionWriterReviewGPT):
    background_product_fields: Tuple[str] = ('research_goal', 'title_and_abstract',
                                             'most_updated_paper_sections:methods',
                                             'most_updated_paper_sections:results')
    max_reviewing_rounds: int = 1
    section_specific_instructions: str = dedent_triple_quote_str("""
        Recap the main results as appearing in the results (see results section above). 
        Where possible, subtly note any novelty in the methodology or findings.
        Discuss the limitations of the study.
        """)


@dataclass
class ConclusionSectionWriterReviewGPT(SectionWriterReviewGPT):
    background_product_fields: Tuple[str] = ('research_goal', 'title_and_abstract',
                                             'most_updated_paper_sections:results',
                                             'most_updated_paper_sections:discussion')
    max_reviewing_rounds: int = 1
    section_specific_instructions: str = dedent_triple_quote_str("""
        Summarize the main results and their implications, impact, and future directions.
        """)
