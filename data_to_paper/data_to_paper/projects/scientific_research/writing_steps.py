import re
from dataclasses import dataclass
from typing import Tuple, List, Set

from data_to_paper.base_steps import LatexReviewBackgroundProductsConverser, \
    CheckExtractionReviewBackgroundProductsConverser
from data_to_paper.base_steps.literature_search import CITATION_REPR_FIELDS, CITATION_REPR_FIELDS_FOR_PRINT
from data_to_paper.latex.tables import get_table_label
from data_to_paper.projects.scientific_research.cast import ScientificAgent
from data_to_paper.projects.scientific_research.scientific_products import ScientificProducts
from data_to_paper.servers.openai_models import ModelEngine
from data_to_paper.servers.types import Citation

from data_to_paper.utils import dedent_triple_quote_str
from data_to_paper.utils.citataion_utils import find_citation_ids
from data_to_paper.utils.nice_list import nicely_join
from data_to_paper.utils.types import ListBasedSet


# TODO: need to generalize this class and move to base steps
class ShowCitationProducts:
    products: ScientificProducts = None
    background_product_fields: Tuple[str, ...] = ()

    def _pre_populate_background(self):
        for content in self.get_repr_citation_products():
            self.comment(content, web_conversation_name=None)
        return super()._pre_populate_background()

    def get_repr_citation_products(self) -> List[str]:
        contents = []
        for field in self.background_product_fields:
            if field.startswith('literature_search') and self.products.is_product_available(field):
                with CITATION_REPR_FIELDS.temporary_set(CITATION_REPR_FIELDS_FOR_PRINT):
                    product = self.products[field]
                    contents.append(f'{product.name}:\n{product.description}')
        return contents


@dataclass
class SectionWriterReviewBackgroundProductsConverser(ShowCitationProducts,
                                                     LatexReviewBackgroundProductsConverser,
                                                     CheckExtractionReviewBackgroundProductsConverser):
    """
    Base class for the writer of a paper section in latex format.
    """
    products: ScientificProducts = None
    background_product_fields: Tuple[str, ...] = ('data_file_descriptions', 'research_goal',
                                                  'codes:data_analysis', 'tables_and_numeric_values', 'results_summary',
                                                  'title_and_abstract')
    product_fields_from_which_response_is_extracted: Tuple[str, ...] = None
    allow_citations_from_step: str = None
    should_remove_citations_from_section: bool = False

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

    def __post_init__(self):
        self.conversation_name = self.conversation_name or nicely_join(self.section_names, separator='_')
        super().__post_init__()

    def _get_available_citations(self) -> List[Citation]:
        if self.allow_citations_from_step is None:
            return []
        return self.products.literature_search[self.allow_citations_from_step].get_citations()

    def _check_citation_ids(self, section: str):
        available_citations = self._get_available_citations()
        available_citations_ids = [citation.bibtex_id for citation in available_citations]
        not_found_citation_ids = [citation_id for citation_id in find_citation_ids(section)
                                  if citation_id not in available_citations_ids]
        if not_found_citation_ids:
            self._raise_self_response_error(f'These citation ids are not correct: {not_found_citation_ids}')

    def _check_section(self, section: str, section_name: str):
        super()._check_section(section, section_name)
        self._check_citation_ids(section)
        self._check_extracted_numbers(section)
        self._check_url_in_text(section)

    def _check_usage_of_unwanted_commands(self, extracted_section: str, unwanted_commands: List[str] = None):
        if self.allow_citations_from_step is None:
            return super()._check_usage_of_unwanted_commands(extracted_section, unwanted_commands)
        return super()._check_usage_of_unwanted_commands(extracted_section, [r'\verb'])

    def write_sections_with_citations(self) -> List[Tuple[str, Set[Citation]]]:
        sections: List[str] = self.run_dialog_and_get_valid_result()
        sections_and_citations = []
        for section in sections:
            sections_and_citations.append(
                (section, ListBasedSet(citation for citation in self._get_available_citations()
                                       if citation.bibtex_id in find_citation_ids(section)))
            )
        return sections_and_citations


@dataclass
class FirstTitleAbstractSectionWriterReviewGPT(SectionWriterReviewBackgroundProductsConverser):
    goal_noun: str = 'title and abstract for a research paper'
    background_product_fields: Tuple[str] = ('general_dataset_description', 'research_goal',
                                             'codes:data_analysis', 'tables_and_numeric_values', 'results_summary')
    max_reviewing_rounds: int = 1
    conversation_name: str = 'title_abstract_section_first'
    latex_instructions: str = dedent_triple_quote_str("""
        Write in tex format including the \\title{} and \\begin{abstract} ... \\end{abstract} commands, \
        and any math or symbols that needs tex escapes.
        """)
    section_specific_instructions: str = dedent_triple_quote_str("""\n
        The Title should: 
        * be short and meaningful.
        * convey the main message, focusing on discovery not on methodology nor on the data source.
        * not include punctuation marks, such as ":,;" characters.

        The Abstract should provide a concise, interesting to read, single-paragraph summary of the paper, \
        with the following structure:
        * short statement of the subject and its importance. 
        * description of the research gap/question/motivation.
        * short, non-technical, description of the dataset used and a non-technical explanation of the methodology.
        * summary of each of the main results. It should summarize each key result which is evident from the tables, \
        but without referring to specific numeric values from the tables.
        * statement of limitations and implications.
        """)
    section_review_specific_instructions: str = "{section_specific_instructions}"

    _raised_colon_error = False  # False to raise ":" error once. True to not raise error at all.

    def _check_section(self, section: str, section_name: str):
        if section_name == 'title':
            if ':' in section and not self._raised_colon_error:
                self._raised_colon_error = True
                self._raise_self_response_error(
                    'Title in {journal_name} typically do not have a colon. '
                    'Can you think of a different title that clearly state a single message without using a colon?')
        if section_name == 'abstract' and section.count('\n') > 2:
            self._raise_self_response_error(f'The abstract should writen as a single paragraph.')
        super()._check_section(section, section_name)


@dataclass
class SecondTitleAbstractSectionWriterReviewGPT(FirstTitleAbstractSectionWriterReviewGPT):
    max_reviewing_rounds: int = 0
    conversation_name: str = 'title_abstract_section_second'
    background_product_fields: Tuple[str] = ('general_dataset_description', 'research_goal',
                                             'paper_sections:results',
                                             'literature_search:writing:20:2',
                                             'title_and_abstract')
    user_initiation_prompt: str = dedent_triple_quote_str("""
        Bases on the material provided above ({actual_background_product_names}), please help me improve the \
        title and abstract for a {journal_name} research paper. 

        {section_specific_instructions}

        I especially want you to:
        (1) Make sure that the abstract clearly states the main results of the paper (see above the Results Section).
        (2) Make sure that the abstract correctly defines the literature gap \
        (see above list of papers in the Literature Search).

        {latex_instructions}
        """)


@dataclass
class IntroductionSectionWriterReviewGPT(SectionWriterReviewBackgroundProductsConverser):
    model_engine: ModelEngine = ModelEngine.GPT4
    background_product_fields: Tuple[str, ...] = ('general_dataset_description', 'title_and_abstract',
                                                  'literature_search_by_scope:writing:background:8:2',
                                                  'literature_search_by_scope:writing:results:6:2',
                                                  'literature_search_by_scope:writing:dataset:4:2',
                                                  'literature_search_by_scope:writing:methods:4:2',
                                                  'paper_sections:methods',
                                                  'paper_sections:results')
    allow_citations_from_step: str = 'writing'
    max_reviewing_rounds: int = 1
    section_specific_instructions: str = dedent_triple_quote_str("""\n
        The introduction should be interesting and pique your reader’s interest. 
        It should be written while citing relevant papers from the Literature Searches above.

        Specifically, the introduction should follow the following multi-paragraph structure:

        * Introduce the topic of the paper and why it is important \
        (cite relevant papers from the above "Literature Search for Background"). 

        * Explain what was already done and known on the topic, and what is then the research gap/question \
        (cite relevant papers from the above "Literature Search for Results"). 

        * State how the current paper addresses this gap/question \
        (cite relevant papers from the above "Literature Search for Dataset").

        * Outline the methodological procedure and briefly state the main findings \
        (cite relevant papers from the above "Literature Search for Methods"). 

        Each of these paragraphs should be 4-6 sentence long.

        Citations should be added in the following format: \\cite{paper_id}.
        Do not add a \\section{References} section, I will add it later manually.

        Note that there is no need to describe limitations, implications, or impact in the introduction.
        """)
    section_review_specific_instructions: str = dedent_triple_quote_str("""\n
        Also, please suggest if there are any additional citations to include from the "Literature Search" above.
        """)


@dataclass
class MethodsSectionWriterReviewGPT(SectionWriterReviewBackgroundProductsConverser):
    background_product_fields: Tuple[str, ...] = ('data_file_descriptions', 'research_goal', 'codes:data_preprocessing',
                                                  'codes:data_analysis', 'title_and_abstract')
    max_reviewing_rounds: int = 0
    enforced_sub_headers: Tuple[str, ...] = ('Data Source', 'Data Preprocessing', 'Data Analysis')

    @property
    def enforced_subheader_prompt(self) -> str:
        if self.enforced_sub_headers is None:
            return ''
        s = f'The Methods section should only have the following {len(self.enforced_sub_headers)} subsections:\n'
        for sub_header in self.enforced_sub_headers:
            s += f'* {sub_header}\n'
        return s

    section_specific_instructions: str = dedent_triple_quote_str("""\n
        The Methods section should have 3 subsections:

        * "Data Source": Describe the data sources, based on the data file descriptions provided above.

        * "Data Preprocessing": Describe preprocessing of the data done by the Python code. Do not include \
        preprocessing steps that were not performed by the code, or that were performed by the code \
        but were not used as basis for the result output.

        * "Data Analysis": Describe the specific analysis steps performed by the Python code to yield the results. \
        Do not be over technical. \
        Do not enumerate the steps as a list; instead, describe the steps in a narrative form.

        Do NOT include any of the following:
        - Missing steps not done by the code.
        - Intermediate analysis steps that were performed but that were not used in further downstream steps.
        - Specific version of software packages, file names, column names.
        - Names of package functions (e.g., do not say "We used sklearn.linear_model.LinearRegression", say instead \
        "We used a linear regression model") 
        - URLs, links or references.
        """)

    section_review_specific_instructions: str = "{section_specific_instructions}"

    def _check_and_extract_result_from_self_response(self, response: str):
        # Warn on "version = ..." :
        # e.g. "version = 1.2.3", "version 1.2.3", "Python 3.7", "Python 3.7.1"
        pattern = r'version(?:\s*=\s*|\s+)(\d+\.\d+(\.\d+)?)|Python\s+(\d+\.\d+)'
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
        return super()._check_and_extract_result_from_self_response(response)

    def run_dialog_and_get_valid_result(self) -> list:
        # Add code availability statement:
        response = [super().run_dialog_and_get_valid_result()[0] +
                    '\\subsection{Code Availability}\n\n'
                    'Custom code used to perform the data preprocessing and analysis, '
                    'as well as the raw code outputs, are provided in Supplementary Methods.']
        return response


@dataclass
class ReferringTablesSectionWriterReviewGPT(SectionWriterReviewBackgroundProductsConverser):
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

        Do not suggest adding missing information, or stating whats missing from the Tables and Numerical Values, \
        only suggest changes that are relevant to the Results section text that are supported by the given \
        Tables and Numerical Values.

        Do not suggest changes to the {goal_noun} that may require data not available in the the \
        Tables and Numerical Values.
        """)

    def _get_table_labels(self, section_name: str) -> List[str]:
        return [get_table_label(table) for table in self.products.tables[section_name]]

    def _check_section(self, section: str, section_name: str):
        table_labels = self._get_table_labels(section_name)
        for table_label in table_labels:
            if table_label not in section:
                self._raise_self_response_error(dedent_triple_quote_str(f"""
                    The {section_name} section should specifically reference each of the Tables that we have.
                    Please make sure we have a sentence addressing Table "{table_label}".
                    The sentence should have a reference like this: "Table~\\ref{{{table_label}}}".
                    """))


@dataclass
class DiscussionSectionWriterReviewGPT(SectionWriterReviewBackgroundProductsConverser):
    model_engine: ModelEngine = ModelEngine.GPT4
    background_product_fields: Tuple[str, ...] = ('title_and_abstract',
                                                  'literature_search_by_scope:writing:background:5:2',
                                                  'literature_search_by_scope:writing:results:8:2',
                                                  'paper_sections:introduction',
                                                  'paper_sections:methods',
                                                  'paper_sections:results')
    allow_citations_from_step: str = 'writing'
    max_reviewing_rounds: int = 1
    section_review_specific_instructions: str = dedent_triple_quote_str("""\n
        Also, please suggest if there are any additional citations to include from the "Literature Search" above.
        """)
    section_specific_instructions: str = dedent_triple_quote_str("""\n
        The Discussion section should follow the following structure:
        * Recap the subject of the study (cite relevant papers from the above "Literature Search for Background").  
        * Recap our methodology (see "Methods" section above) and the main results (see "Results" section above), \
        and compare them to the results from prior literature (see above "Literature Search for Results"). 
        * Discuss the limitations of the study.
        * End with a concluding paragraph summarizing the main results, their implications and impact, \
        and future directions.

        Citations should be added in the following format: \\cite{paper_id}.
        Do not add a \\section{References} section, I will add it later manually.
        """)


@dataclass
class ConclusionSectionWriterReviewGPT(SectionWriterReviewBackgroundProductsConverser):
    background_product_fields: Tuple[str, ...] = ('research_goal', 'title_and_abstract',
                                                  'paper_sections:results',
                                                  'paper_sections:discussion')
    max_reviewing_rounds: int = 1
    section_specific_instructions: str = dedent_triple_quote_str("""\n
        Summarize the main results and their implications, impact, and future directions.
        """)
