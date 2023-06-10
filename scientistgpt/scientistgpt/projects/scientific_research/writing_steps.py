import re
from dataclasses import dataclass, field
from typing import Tuple

from scientistgpt.base_steps import LatexReviewBackgroundProductsConverser, \
    CheckExtractionReviewBackgroundProductsConverser
from scientistgpt.projects.scientific_research.cast import ScientificAgent
from scientistgpt.servers.openai_models import ModelEngine
from scientistgpt.utils import dedent_triple_quote_str
from scientistgpt.utils.nice_list import nicely_join


@dataclass
class SectionWriterReviewBackgroundProductsConverser(LatexReviewBackgroundProductsConverser,
                                                     CheckExtractionReviewBackgroundProductsConverser):
    """
    Base class for the writer of a paper section in latex format.
    """
    background_product_fields: Tuple[str, ...] = ('data_file_descriptions', 'research_goal',
                                                  'codes:data_analysis', 'tables_and_numeric_values', 'results_summary',
                                                  'title_and_abstract')
    product_fields_from_which_response_is_extracted: Tuple[str, ...] = None

    fake_performer_request_for_help: str = \
        'Hi {user_skin_name}, could you please help me {goal_verb} the {pretty_section_names} for my paper?'

    max_reviewing_rounds: int = 1
    goal_noun: str = '{pretty_section_names} section'
    conversation_name: str = None
    goal_verb: str = 'write'
    performer: str = 'scientific writer'
    reviewer: str = 'scientific reviewer'
    assistant_agent: ScientificAgent = ScientificAgent.Performer
    user_agent: ScientificAgent = ScientificAgent.Writer
    section_specific_instructions: str = ''
    section_review_specific_instructions: str = ''
    journal_name: str = 'Nature Communications'

    system_prompt: str = dedent_triple_quote_str("""
        You are a data-scientist with experience writing accurate scientific research papers.

        You will write a scientific article for the journal {journal_name}, following the instructions below:
        1. Write the article section by section: Abstract, Introduction, Results, Discussion, and Methods.
        2. Write every section of the article in scientific language, in `.tex` format.
        3. Write the article in a way that is fully consistent with the scientific products we have.
        4. Write the text without adding any citations (we will only add citations in a later stage).
        """)

    user_initiation_prompt: str = dedent_triple_quote_str("""
        Based on the material provided above ({actual_background_product_names}), \
        please {goal_verb} only the {goal_noun} for a {journal_name} article.
        Do not write any other parts!
        {section_specific_instructions}
        {latex_instructions}
        """)

    latex_instructions: str = dedent_triple_quote_str("""
        Write in tex format including the \\section{} command, and any math or symbols that needs tex escapes.
        """)

    termination_phrase: str = 'I hereby approve the {goal_noun}.'

    other_system_prompt: str = dedent_triple_quote_str("""
        You are a reviewer for a scientist who is writing a scientific paper about their data analysis results.
        Your job is to provide constructive bullet-point feedback.
        We will write each section of the research paper separately. 
        If you feel that the paper section does not need further improvements, you should reply only with:
        "{termination_phrase}".
    """)

    sentence_to_add_at_the_end_of_reviewer_response: str = dedent_triple_quote_str("""
        Please correct your response according to my feedback and send back a complete rewrite \
        of the {pretty_section_names}.
        Make sure to send the full corrected {pretty_section_names}, not just the parts that were revised.
    """)

    sentence_to_add_at_the_end_of_performer_response: str = dedent_triple_quote_str("""
        Please provide a bullet-point list of constructive feedback on the above {pretty_section_names} \
        for my paper. Do not provide positive feedback, only provide actionable instructions in bullet points. 
        In particular, make sure that the section is correctly grounded in the information provided above.
        If you find any inconsistencies or discrepancies, please mention them explicitly in your feedback.
        {section_review_specific_instructions}
        
        If you don't see any flaws, respond solely the following "{termination_phrase}".
        
        IMPORTANT: You should EITHER provide bullet-point feedback, OR respond solely with "{termination_phrase}"; 
        you should not do both.
        """)

    def __post_init__(self):
        self.conversation_name = self.conversation_name or nicely_join(self.section_names, separator='_')
        super().__post_init__()

    def _check_section(self, section: str, section_name: str):
        super()._check_section(section, section_name)
        self._check_extracted_numbers(section)


@dataclass
class FirstTitleAbstractSectionWriterReviewGPT(SectionWriterReviewBackgroundProductsConverser):
    goal_noun: str = 'title and abstract for a research paper'
    background_product_fields: Tuple[str] = ('general_dataset_description', 'research_goal',
                                             'codes:data_analysis', 'tables_and_numeric_values', 'results_summary')
    max_reviewing_rounds: int = 2
    conversation_name: str = 'title_abstract_section_first'
    latex_instructions: str = dedent_triple_quote_str("""
        Write in tex format including the \\title{} and \\begin{abstract} ... \\end{abstract} commands, \
        and any math or symbols that needs tex escapes.
        """)
    section_specific_instructions: str = dedent_triple_quote_str("""
        The title should be short and meaningful. It should focus on the main result of the paper and not on the \
        methods or the data.
        The abstract should provide a short and concise summary of the paper. 
        It should include short background on the research question and motivation, \
        short intro to the dataset used and a non-technical explanation of the methodology.
        It should then provide a short summary of the main results and their implications.
        Do not include numeric values like p-values or effect sizes in the abstract.
        """)

    _raised_colon_error = True  # False to raise ":" error once. True to not raise error at all.

    def _check_section(self, section: str, section_name: str):
        if section_name == 'title':
            if ':' in section and not self._raised_colon_error:
                self._raised_colon_error = True
                self._raise_self_response_error(
                    'Title in {journal_name} typically do not have a colon. '
                    'Can you think of a different title that clearly state a single message without using a colon?')
        super()._check_section(section, section_name)


@dataclass
class SecondTitleAbstractSectionWriterReviewGPT(FirstTitleAbstractSectionWriterReviewGPT):
    max_reviewing_rounds: int = 0
    conversation_name: str = 'title_abstract_section_second'
    background_product_fields: Tuple[str] = ('general_dataset_description', 'research_goal',
                                             'most_updated_paper_sections:results', 'title_and_abstract')
    user_initiation_prompt: str = dedent_triple_quote_str("""
        Bases on the material provided above ({actual_background_product_names}), please help me improve the \
        title and abstract for a research paper.
        We are writing for {journal_name}. 
        
        {section_specific_instructions}
        
        I especially want you to read the Results section above and make sure that the abstract clearly states \
        the main results of the paper.
        
        {latex_instructions}
        """)


@dataclass
class IntroductionSectionWriterReviewGPT(SectionWriterReviewBackgroundProductsConverser):
    background_product_fields: Tuple[str, ...] = ('general_dataset_description', 'title_and_abstract',
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
class MethodsSectionWriterReviewGPT(SectionWriterReviewBackgroundProductsConverser):
    background_product_fields: Tuple[str, ...] = ('data_file_descriptions', 'research_goal', 'codes:data_preprocessing',
                                                  'codes:data_analysis', 'title_and_abstract')
    max_reviewing_rounds: int = 1
    enforced_sub_headers: Tuple[str, ...] = ('Data Source', 'Data Preprocessing', 'Data Analysis')

    @property
    def enforced_subheader_prompt(self) -> str:
        if self.enforced_sub_headers is None:
            return ''
        s = f'The Methods section should only have the following {len(self.enforced_sub_headers)} subsections:\n'
        for sub_header in self.enforced_sub_headers:
            s += f'* {sub_header}\n'
        return s

    section_specific_instructions: str = dedent_triple_quote_str("""
        Make sure that you are only referring to analysis steps that are explicitly performed by the \
        data preprocessing code and data analysis code (see Python code blocks above).

        Focus on the methods that were used to achieve the research goal.
        
        {enforced_subheader_prompt}
        """)

    section_review_specific_instructions: str = dedent_triple_quote_str("""\n
        Specifically, pay attention to:

        - Description of analysis steps that were not explicitly performed by the analysis Python codes \
        (provided above), like certain data cleaning processes.
        - References to variables and data files that were not used in the analysis.
        
        {enforced_subheader_prompt}
        """)

    def _check_and_extract_result_from_self_response(self, response: str):
        # Warn on "version = ..." :
        pattern = r'version(?:\s*=\s*|\s+)(\d+\.\d+\.\d+)'  # e.g. "version = 1.2.3" or "version 1.2.3"
        if re.findall(pattern, response):
            self._raise_self_response_error(
                f'Do not mention specific version of software packages.')

        # Check subsection headings:
        pattern = r'\\subsection{([^}]*)}'
        matches = re.findall(pattern, response)
        if set(matches) != {'Data Source', 'Data Preprocessing', 'Data Analysis'}:
            self._raise_self_response_error(
                f'The Methods section should only have the following 3 subsections: '
                f'Data Source, Data Preprocessing, Data Analysis. ')

        # Add code availability statement:
        response += '\n\n\\subsection{Code Availability}\n\n' \
                    'Custom code used to perform the data preprocessing and analysis, ' \
                    'as well as the raw code output outputs, are provided in Supplementary Methods.'

        return super()._check_and_extract_result_from_self_response(response)


@dataclass
class ReferringTablesSectionWriterReviewGPT(SectionWriterReviewBackgroundProductsConverser):
    user_agent: ScientificAgent = ScientificAgent.TableExpert
    background_product_fields: Tuple[str, ...] = \
        ('title_and_abstract', 'tables_and_numeric_values')
    product_fields_from_which_response_is_extracted: Tuple[str, ...] = \
        ('title_and_abstract', 'tables_and_numeric_values')
    max_reviewing_rounds: int = 1
    section_specific_instructions: str = dedent_triple_quote_str("""\n
        As you write the results, \
        refer to the Tables by their labels and explain their content, but do not add the tables themselves \
        (I will add the tables later manually).

        You should typically have a separate paragraph describing for each Table. In each such paragraph, \
        indicate the motivation/question for the analysis, the methodology, and only then describe the results.
        
        It is often nice to have a story-like flow between the paragraphs, so that the reader can follow the \
        analysis process with emphasis on the reasoning/motivation behind each analysis step. 
        For example, the first sentence of each paragraph can be a story-guiding sentences like: 
        "First, to understand whether xxx, we conducted a simple analysis of ..."; "Then, to test yyy, we performed a \
        ..."; "Finally, to further verify the effect of zzz, we tested whether ...". 
                
        You can also extract and use any of the key Numerical Values provided above that you think are \
        scientifically meaningful. Note though that, unlike the Tables, these Numerical Values are not going to be \
        added as a part of the paper, so you should explicitly mention any important values as an integral part of \
        the text.
        When mentioning p-values, use the $<$ symbol to indicate that the p-value is smaller than the relevant value, \
        in scientific writing it is not common to write 0 as a p-value.

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

    def _get_latex_section_from_response(self, response: str, section_name: str) -> str:
        section = super()._get_latex_section_from_response(response, section_name)
        return self._check_extracted_numbers(section)

@dataclass
class DiscussionSectionWriterReviewGPT(SectionWriterReviewBackgroundProductsConverser):
    background_product_fields: Tuple[str, ...] = ('title_and_abstract',
                                                  'most_updated_paper_sections:methods',
                                                  'most_updated_paper_sections:results')
    max_reviewing_rounds: int = 1
    section_specific_instructions: str = dedent_triple_quote_str("""
        Recap the main results as appearing in the Results section (see above). 
        Where possible, subtly note any novelty in the methodology or findings.
        Discuss the limitations of the study.
        End with a concluding paragraph summarizing the main results and their implications, impact, \
        and future directions.
        """)


@dataclass
class ConclusionSectionWriterReviewGPT(SectionWriterReviewBackgroundProductsConverser):
    background_product_fields: Tuple[str, ...] = ('research_goal', 'title_and_abstract',
                                                  'most_updated_paper_sections:results',
                                                  'most_updated_paper_sections:discussion')
    max_reviewing_rounds: int = 1
    section_specific_instructions: str = dedent_triple_quote_str("""
        Summarize the main results and their implications, impact, and future directions.
        """)
