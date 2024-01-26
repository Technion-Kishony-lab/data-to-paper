import re
from dataclasses import dataclass, field
from typing import Tuple, List, Set, Optional, Iterable

from data_to_paper.base_steps import LatexReviewBackgroundProductsConverser, \
    CheckExtractionReviewBackgroundProductsConverser
from data_to_paper.base_steps.exceptions import FailedCreatingProductException
from data_to_paper.latex.tables import get_table_label
from data_to_paper.research_types.scientific_research.cast import ScientificAgent
from data_to_paper.research_types.scientific_research.scientific_products import ScientificProducts, \
    DEFAULT_LITERATURE_SEARCH_STYLE
from data_to_paper.servers.model_engine import ModelEngine
from data_to_paper.research_types.scientific_research.model_engines import get_model_engine_for_class
from data_to_paper.servers.custom_types import Citation

from data_to_paper.utils import dedent_triple_quote_str
from data_to_paper.utils.citataion_utils import find_citation_ids
from data_to_paper.utils.nice_list import nicely_join
from data_to_paper.utils.print_to_file import print_and_log
from data_to_paper.utils.types import ListBasedSet


# TODO: need to generalize this class and move to base steps
class ShowCitationProducts:
    products: ScientificProducts = None
    background_product_fields: Tuple[str, ...] = ()

    allow_citations_from_step: str = None

    def _pre_populate_background(self):
        for content in self.get_repr_citation_products():
            self.comment(content, web_conversation_name=None)
        return super()._pre_populate_background()

    def get_repr_citation_products(self) -> List[str]:
        contents = []
        for product_field in self.background_product_fields:
            if product_field.startswith('literature_search') and self.products.is_product_available(product_field):
                with DEFAULT_LITERATURE_SEARCH_STYLE.temporary_set('print'):
                    product = self.products[product_field]
                    contents.append(f'{product.name}:\n{product.description}')
        return contents

    def _get_available_citations(self) -> Iterable[Citation]:
        if self.allow_citations_from_step is None:
            return []
        return self.products.literature_search[self.allow_citations_from_step].get_citations()

    def _get_allowed_bibtex_citation_ids(self) -> List[str]:
        return [citation.bibtex_id for citation in self._get_available_citations()]


@dataclass
class SectionWriterReviewBackgroundProductsConverser(ShowCitationProducts,
                                                     LatexReviewBackgroundProductsConverser,
                                                     CheckExtractionReviewBackgroundProductsConverser):
    """
    Base class for the writer of a paper section in latex format.
    """
    products: ScientificProducts = None
    background_product_fields: Tuple[str, ...] = ('data_file_descriptions', 'research_goal',
                                                  'codes:data_analysis', 'tables', 'additional_results',
                                                  'title_and_abstract')
    product_fields_from_which_response_is_extracted: Tuple[str, ...] = None
    should_remove_citations_from_section: bool = True
    un_allowed_commands: Tuple[str, ...] = (r'\verb', r'\begin{figure}')

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

    latex_instructions: str = dedent_triple_quote_str("""
        Write in tex format, escaping any math or symbols that needs tex escapes.
        """)

    request_triple_quote_block: Optional[str] = dedent_triple_quote_str("""
        The {goal_noun} should be enclosed within triple-backtick "latex" code block, like this:

        ```latex
        \\section{<section name>}
        <your latex-formatted writing here>
        ```
        """)

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
        {request_triple_quote_block}
        """)

    termination_phrase: str = 'The {goal_noun} does not require any changes'

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
        or other parts of the paper, like LaTex Tables or Python code, provided above.

        If you don't see any flaws, respond solely with "{termination_phrase}".

        IMPORTANT: You should EITHER provide bullet-point feedback, or respond solely with "{termination_phrase}"; \
        If you chose to provide bullet-point feedback then DO NOT include "{termination_phrase}".
        """)

    forbidden_phrases: Tuple[Tuple[str, bool], ...] = (
        # (phrase, match_case)
        ('Acknowledgments', True, ),
        ('Data Availability', False, ),
        ('Author Contributions', False, ),
        ('Competing Interests', False, ),
        ('Additional Information', False, ),
        ('References', True, ),
        ('Supplementary', False, ),
    )

    aborting_phrases: Tuple[Tuple[str, bool], ...] = (
        # (phrase, match_case)
        ('[unknown', False),
        ('<unknown', False),
        ('[insert', False),
        ('<insert', False),
        ('[missing', False),
        ('<missing', False),
        ('[to be', False),
        ('<to be', False),
        ('xx', False),
        ('xxx', False),
    )

    allow_subsections: bool = False

    def __post_init__(self):
        self.conversation_name = self.conversation_name or nicely_join(self.section_names, separator='_')
        super().__post_init__()

    def _check_allowed_subsections(self, section: str):
        if not self.allow_subsections:
            if r'\subsection' in section:
                self._raise_self_response_error('Do not include subsections in the {goal_noun}')

    @staticmethod
    def _is_pharse_in_section(section: str, phrase: str, match_case: bool) -> bool:
        if match_case:
            return phrase in section
        else:
            return phrase.lower() in section.lower()

    def _check_forbidden_phrases(self, section: str):
        used_forbidden_phrases = [
            phrase for phrase, match_case in self.forbidden_phrases
            if self._is_pharse_in_section(section, phrase, match_case)
        ]
        if used_forbidden_phrases:
            self._raise_self_response_error('Do not include: {}'.format(
                nicely_join(used_forbidden_phrases, wrap_with='"', separator=', ')))

    def _check_for_aborting_phrases(self, section: str):
        used_aborting_phrases = [
            phrase for phrase, match_case in self.aborting_phrases
            if self._is_pharse_in_section(section, phrase, match_case)
        ]
        if used_aborting_phrases:
            raise FailedCreatingProductException("The LLM requires unknown values to write the section.")

    def _check_and_refine_section(self, section: str, section_name: str) -> str:
        self._check_for_aborting_phrases(section)
        section = super()._check_and_refine_section(section, section_name)
        self._check_extracted_numbers(section)
        self._check_url_in_text(section)
        self._check_forbidden_phrases(section)
        self._check_allowed_subsections(section)
        return section

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
    background_product_fields: Tuple[str] = ('general_dataset_description',
                                             'codes:data_analysis', 'tables', 'additional_results')
    max_reviewing_rounds: int = 1
    conversation_name: str = 'title_abstract_section_first'

    request_triple_quote_block: Optional[str] = dedent_triple_quote_str("""
        The {goal_noun} should be enclosed within triple-backtick "latex" code block, like this:

        ```latex
        \\title{<your latex-formatted paper title here>}

        \\begin{abstract}
        <your latex-formatted abstract here>
        \\end{abstract}
        ```
        """)

    # no need for triple quote block in title and abstract because they have clear begin-end wraps
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

    def _check_and_refine_section(self, section: str, section_name: str) -> str:
        if section_name == 'title':
            if ':' in section and not self._raised_colon_error:
                self._raised_colon_error = True
                self._raise_self_response_error(
                    'Titles of manuscripts in {journal_name} typically do not have a colon. '
                    'Can you think of a different title that clearly state a single message without using a colon?')
        if section_name == 'abstract' and section.count('\n') > 2:
            self._raise_self_response_error(f'The abstract should writen as a single paragraph.')
        return super()._check_and_refine_section(section, section_name)


@dataclass
class SecondTitleAbstractSectionWriterReviewGPT(FirstTitleAbstractSectionWriterReviewGPT):
    max_reviewing_rounds: int = 0
    conversation_name: str = 'title_abstract_section_second'
    background_product_fields: Tuple[str] = ('general_dataset_description',
                                             'paper_sections:results',
                                             'literature_search:writing:background',
                                             'literature_search:writing:dataset',
                                             'literature_search:writing:results',
                                             'title_and_abstract')
    user_initiation_prompt: str = dedent_triple_quote_str("""
        Bases on the material provided above ({actual_background_product_names}), please help me improve the \
        title and abstract for a {journal_name} research paper. 

        {section_specific_instructions}

        I especially want you to:
        (1) Make sure that the abstract clearly states the main results of the paper \
        (see above the {paper_sections:results}).
        (2) Make sure that the abstract correctly defines the literature gap/question/motivation \
        (see above Literature Searches for list of related papers).

        {latex_instructions}
        {request_triple_quote_block}
        """)


@dataclass
class IntroductionSectionWriterReviewGPT(SectionWriterReviewBackgroundProductsConverser):
    background_product_fields: Tuple[str, ...] = ('general_dataset_description', 'title_and_abstract',
                                                  'literature_search:writing:background',
                                                  'literature_search:writing:results',
                                                  'literature_search:writing:dataset',
                                                  'literature_search:writing:methods',
                                                  'paper_sections:methods',
                                                  'paper_sections:results')
    allow_citations_from_step: str = 'writing'
    should_remove_citations_from_section: bool = False
    max_reviewing_rounds: int = 1
    model_engine: ModelEngine = \
        field(default_factory=lambda: get_model_engine_for_class(IntroductionSectionWriterReviewGPT))
    section_specific_instructions: str = dedent_triple_quote_str("""\n
        The introduction should be interesting and pique your reader’s interest. 
        It should be written while citing relevant papers from the Literature Searches above.

        Specifically, the introduction should follow the following multi-paragraph structure:

        * Introduce the topic of the paper and why it is important \
        (cite relevant papers from the above "{literature_search:writing:background}"). 

        * Explain what was already done and known on the topic, and what is then the research gap/question \
        (cite relevant papers from the above "{literature_search:writing:results}"). If there is only a minor gap, \
        you can use language such as "Yet, it is still unclear ...", "However, less is known about ...", \
        etc.

        * State how the current paper addresses this gap/question \
        (cite relevant papers from the above "{literature_search:writing:dataset}" and \
        "{literature_search:writing:results}").

        * Outline the methodological procedure and briefly state the main findings \
        (cite relevant papers from the above "{literature_search:writing:methods}")

        Note: each of these paragraphs should be 5-6 sentence long. Do not just write short paragraphs with less \
        than 5 sentences!  

        Citations should be added in the following format: \\cite{paper_id}.
        Do not add a \\section{References} section, I will add it later manually.

        Note that it is not advisable to write about limitations, implications, or impact in the introduction.
        """)
    section_review_specific_instructions: str = dedent_triple_quote_str("""\n
        Also, please suggest if you see any specific additional citations that are adequate to include \
        (from the Literature Searches above).
        """)


@dataclass
class MethodsSectionWriterReviewGPT(SectionWriterReviewBackgroundProductsConverser):
    background_product_fields: Tuple[str, ...] = ('data_file_descriptions', 'research_goal', 'codes:data_preprocessing',
                                                  'codes:data_analysis', 'title_and_abstract')
    max_reviewing_rounds: int = 0
    enforced_sub_headers: Tuple[str, ...] = ('Data Source', 'Data Preprocessing', 'Data Analysis')
    allow_subsections: bool = True

    @property
    def enforced_subheader_prompt(self) -> str:
        if self.enforced_sub_headers is None:
            return ''
        s = f'The Methods section should only have the following {len(self.enforced_sub_headers)} subsections:\n'
        for sub_header in self.enforced_sub_headers:
            s += f'* {sub_header}\n'
        return s

    section_specific_instructions: str = dedent_triple_quote_str("""\n
        The Methods section should be enclosed within triple-backtick "latex" code block \
        and have 3 subsections, as follows: 

        ```latex
        \\section{Methods}

        \\subsection{Data Source}
        - Describe our data sources (see above "{data_file_descriptions}")

        \\subsection{Data Preprocessing}
        - Describe preprocessing of the data done by the Python code (see above "{codes:data_analysis}").
        - Do not include preprocessing steps that were not performed by the code. 
        - Do not include preprocessing steps that were performed by the code, but were not used as basis \
        for further analysis affecting the result output.

        \\subsection{Data Analysis}
        - Describe each of the specific analysis steps performed by the Python code to yield the results.
        - Do not be over technical.
        - Do not enumerate the steps as a list; instead, describe the steps in a narrative form.
        ```

        Throughout the Methods section, do NOT include any of the following:
        - Missing steps not done by the code.
        - Specific version of software packages, file names, column names.
        - Names of package functions (e.g., do not say "We used sklearn.linear_model.LinearRegression", say instead \
        "We used a linear regression model") 
        - URLs, links or references.""")

    request_triple_quote_block: str = dedent_triple_quote_str("""
        Remember to enclose the Methods section within triple-backtick "latex" code block.
        """)

    latex_instructions: str = ''

    section_review_specific_instructions: str = "{section_specific_instructions}"

    def _check_extracted_result_and_get_valid_result(self, extracted_result: List[str]):
        # Warn on "version = ..." :
        # e.g. "version = 1.2.3", "version 1.2.3", "Python 3.7", "Python 3.7.1"
        response = self._get_fresh_looking_response('', extracted_result)
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
        return super()._check_extracted_result_and_get_valid_result(extracted_result)

    def run_dialog_and_get_valid_result(self) -> list:
        # Add code availability statement:
        response = [super().run_dialog_and_get_valid_result()[0] +
                    '\\subsection{Code Availability}\n\n'
                    'Custom code used to perform the data preprocessing and analysis, '
                    'as well as the raw code outputs, are provided in Supplementary Methods.']
        return response


@dataclass
class ReferringTablesSectionWriterReviewGPT(SectionWriterReviewBackgroundProductsConverser):
    forbidden_phrases: Tuple[Tuple[str, bool], ...] = \
        SectionWriterReviewBackgroundProductsConverser.forbidden_phrases + \
        (
            ('In conclusions', True),
            ('Future research', False),
            ('Future work', False),
            ('Future studies', False),
            ('Future directions', False),
            ('Limitations', False),
    )
    # (phrase, match_case)

    background_product_fields: Tuple[str, ...] = \
        ('title_and_abstract', 'data_file_descriptions', 'codes:data_analysis', 'tables', 'additional_results')
    product_fields_from_which_response_is_extracted: Tuple[str, ...] = \
        ('data_file_descriptions', 'codes:data_analysis', 'tables', 'additional_results')
    max_reviewing_rounds: int = 1
    section_specific_instructions: str = dedent_triple_quote_str("""\n
        Use the following guidelines when writing the Results:

        * Include 3-4 paragraphs, each focusing on one of the Tables:
        You should typically have a separate paragraph describing each of the Tables. \
        In each such paragraph, indicate the motivation/question for the analysis, the methodology, \
        and only then describe the results. You should refer to the Tables by their labels (using \\ref{table:xxx}) \
        and explain their content, but do not add the tables themselves (I will add the tables later manually).

        * Story-like flow: 
        It is often nice to have a story-like flow between the paragraphs, so that the reader \
        can follow the analysis process with emphasis on the reasoning/motivation behind each analysis step. 
        For example, the first sentence of each paragraph can be a story-guiding sentences like: 
        "First, to understand whether xxx, we conducted a simple analysis of ..."; "Then, to test yyy, we performed a \
        ..."; "Finally, to further verify the effect of zzz, we tested whether ...".

        * Conclude with a summary of the results:
        You can summarize the results at the end, with a sentence like: "In summary, these results show ...", \
        or "Taken together, these results suggest ...".
        IMPORTANT NOTE: Your summary SHOULD NOT include a discussion of conclusions, implications, limitations, \
        or of future work.
        (These will be added later as part the Discussion section, not the Results section). 

        * Numeric values:
        You can extract and mention numeric values from the latex Tables as well as from the \
        "{additional_results}" listed above. If you are mentioning a numeric value that is not explicitly \
        mentioned in the Tables or in "{additional_results}", but is rather derived from them, \
        you should provide it using the \\num command. For example:
        "Our regression analysis shows a coefficient of 2.0 (SE=0.3, p-value $<$ 1e-6), \
        corresponding to an odds ratio of \\num{exp(2.0)} (CI: [\\num{exp(2.0 - 2 * 0.3)}, \\num{exp(2.0 + 2 * 0.3)}])."

        * p-values:
        When mentioning p-values, use the $<$ symbol to indicate that the p-value is smaller than the \
        relevant value.

        * Accuracy: 
        Make sure that you are only mentioning details that are explicitly found within the Tables and \
        Numerical Values.

        * Unknown values:
        If we need to include a numeric value that was not calculated or is not explicitly given in the \
        Tables or "{additional_results}", and cannot be derived from them, \
        then indicate `[unknown]` instead of the numeric value. 

        For example:
        "The regression coefficient for the anti-cancer drugs was [unknown]."
        """)
    section_review_specific_instructions: str = dedent_triple_quote_str("""
        Specifically, pay attention to:
        whether the {goal_noun} contains only information that is explicitly extracted from the \
        "{tables}" and "{additional_results}" provided above. \

        Compare the numbers in the {goal_noun} with the numbers in the Tables and Numerical Values and explicitly \
        mention any discrepancies that need to be fixed.

        Do not suggest adding missing information, or stating whats missing from the Tables and Numerical Values, \
        only suggest changes that are relevant to the Results section itself and that are supported by the given \
        Tables and Numerical Values.

        Do not suggest changes to the {goal_noun} that may require data not available in the the \
        Tables and Numerical Values.
        """)

    def _get_table_labels(self, section_name: str) -> List[str]:
        return [get_table_label(table) for table in self.products.tables[section_name]]

    def _check_and_refine_section(self, section: str, section_name: str) -> str:
        result = super()._check_and_refine_section(section, section_name)
        table_labels = self._get_table_labels(section_name)
        for table_label in table_labels:
            if table_label not in section:
                self._raise_self_response_error(dedent_triple_quote_str(f"""
                    The {section_name} section should specifically reference each of the Tables that we have.
                    Please make sure we have a sentence addressing Table "{table_label}".
                    The sentence should have a reference like this: "Table~\\ref{{{table_label}}}".
                    """))
        return result


@dataclass
class DiscussionSectionWriterReviewGPT(SectionWriterReviewBackgroundProductsConverser):
    background_product_fields: Tuple[str, ...] = ('general_dataset_description',
                                                  'title_and_abstract',
                                                  'literature_search:writing:background',
                                                  'literature_search:writing:results',
                                                  'paper_sections:introduction',
                                                  'paper_sections:methods',
                                                  'paper_sections:results')
    allow_citations_from_step: str = 'writing'
    should_remove_citations_from_section: bool = False
    max_reviewing_rounds: int = 1
    model_engine: ModelEngine = \
        field(default_factory=lambda: get_model_engine_for_class(DiscussionSectionWriterReviewGPT))
    section_review_specific_instructions: str = dedent_triple_quote_str("""\n
        Also, please suggest if you see any specific additional citations that are adequate to include \
        (from the Literature Searches above).
        """)
    section_specific_instructions: str = dedent_triple_quote_str("""\n
        The Discussion section should follow the following structure:
        * Recap the subject of the study (cite relevant papers from the above "{literature_search:writing:background}").  
        * Recap our methodology (see "Methods" section above) and the main results \
        (see "{paper_sections:results}" above), \
        and compare them to the results from prior literature (see above "{literature_search:writing:results}"). 
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
