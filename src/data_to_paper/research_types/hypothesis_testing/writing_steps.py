import re
from dataclasses import dataclass
from typing import Tuple, List, Set, Iterable

from data_to_paper.base_steps import LatexReviewBackgroundProductsConverser, \
    CheckReferencedNumericReviewBackgroundProductsConverser
from data_to_paper.base_steps.exceptions import FailedCreatingProductException
from data_to_paper.base_steps.literature_search import GET_LITERATURE_SEARCH_FOR_PRINT
from data_to_paper.latex.tables import get_displayitem_label
from data_to_paper.research_types.hypothesis_testing.cast import ScientificAgent
from data_to_paper.research_types.hypothesis_testing.scientific_products import ScientificProducts
from data_to_paper.servers.custom_types import Citation

from data_to_paper.text import dedent_triple_quote_str
from data_to_paper.latex.citataion_utils import find_citation_ids
from data_to_paper.utils.nice_list import nicely_join
from data_to_paper.utils.types import ListBasedSet


# TODO: need to generalize this class and move to base steps
class ShowCitationProducts:
    products: ScientificProducts = None
    background_product_fields: Tuple[str, ...] = ()

    allow_citations_from_step: str = None

    def _pre_populate_background(self):
        for content in self.get_repr_citation_products():
            self.comment(content)
        return super()._pre_populate_background()

    def get_repr_citation_products(self) -> List[str]:
        contents = []
        for product_field in self.background_product_fields:
            if product_field.startswith('literature_search') and self.products.is_product_available(product_field):
                with GET_LITERATURE_SEARCH_FOR_PRINT.temporary_set(True):
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
                                                     CheckReferencedNumericReviewBackgroundProductsConverser):
    """
    Base class for the writer of a paper section in latex format.
    """
    products: ScientificProducts = None
    background_product_fields: Tuple[str, ...] = ('data_file_descriptions_no_headers', 'research_goal',
                                                  'codes:data_analysis', 'latex_displayitems', 'additional_results',
                                                  'title_and_abstract')
    product_fields_from_which_response_is_extracted: Tuple[str, ...] = None
    should_remove_citations_from_section: bool = True
    un_allowed_commands: Tuple[str, ...] = (r'\verb', r'\begin{figure}')

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

    your_response_should_be_formatted_as: str = dedent_triple_quote_str("""
        a triple-backtick "latex" block, like this:

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

    mission_prompt: str = dedent_triple_quote_str("""
        Based on the material provided above ({actual_background_product_names}), \t
        please {goal_verb} only the {goal_noun} for a {journal_name} article.
        Do not write any other parts!
        {section_specific_instructions}
        {latex_instructions}
        The {goal_noun} should be formatted as {your_response_should_be_formatted_as}
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
        Please provide a bullet-point list of constructive feedback on the above {pretty_section_names} \t
        for my paper. Do not provide positive feedback, only provide actionable instructions for improvements in \t
        bullet points. 
        In particular, make sure that the section is correctly grounded in the information provided above.
        If you find any inconsistencies or discrepancies, please mention them explicitly in your feedback.
        {section_review_specific_instructions}

        You should only provide feedback on the {pretty_section_names}. Do not provide feedback on other sections \t
        or other parts of the paper, like LaTex Tables or Python code, provided above.

        If you don't see any flaws, respond solely with "{termination_phrase}".

        IMPORTANT: You should EITHER provide bullet-point feedback, or respond solely with "{termination_phrase}"; \t
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
        self.conversation_name = self.conversation_name or 'Writing: ' + \
            nicely_join([name.title() for name in self.section_names], separator=', ', last_separator=' and ')
        super().__post_init__()

    def _check_allowed_subsections(self, section: str):
        if not self.allow_subsections:
            if r'\subsection' in section:
                self._raise_self_response_error(
                    title='# Subsections are not allowed',
                    error_message='Do not include subsections in the {goal_noun}')

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
            self._raise_self_response_error(
                title='# Forbidden phrases',
                error_message='Do not include: {}'.format(
                    nicely_join(used_forbidden_phrases, wrap_with='"', separator=', ')))

    def _check_for_aborting_phrases(self, section: str):
        used_aborting_phrases = [
            phrase for phrase, match_case in self.aborting_phrases
            if self._is_pharse_in_section(section, phrase, match_case)
        ]
        if used_aborting_phrases:
            raise FailedCreatingProductException(f"The LLM requires unknown values to write the section; "
                                                 f"it used the following aborting phrases:\n{used_aborting_phrases}")

    def _check_and_refine_section(self, section: str, section_name: str) -> str:
        self._check_for_aborting_phrases(section)
        section = super()._check_and_refine_section(section, section_name)
        self._check_extracted_numbers(section)
        self._check_url_in_text(section)
        self._check_forbidden_phrases(section)
        self._check_allowed_subsections(section)
        return section

    def write_sections_with_citations(self) -> List[Tuple[str, Set[Citation]]]:
        sections: List[str] = self.run_and_get_valid_result()
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
                                             'codes:data_analysis', 'latex_displayitems', 'additional_results')
    max_reviewing_rounds: int = 1
    conversation_name: str = 'Writing: Title and Abstract (first draft)'

    your_response_should_be_formatted_as: str = dedent_triple_quote_str("""
        a triple-backtick "latex" block, like this:

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

        The Abstract should provide a concise, interesting to read, single-paragraph summary of the paper, \t
        with the following structure:
        * short statement of the subject and its importance. 
        * description of the research gap/question/motivation.
        * short, non-technical, description of the dataset used and a non-technical explanation of the methodology.
        * summary of each of the main results. Summarize each key result which is evident from the displayitems, \t
        but without referring to specific numeric values from the displayitems.
        * statement of limitations and implications.
        """)
    section_review_specific_instructions: str = "{section_specific_instructions}"

    _raised_colon_error = False  # False to raise ":" error once. True to not raise error at all.

    def _check_and_refine_section(self, section: str, section_name: str) -> str:
        if section_name == 'title':
            if ':' in section and not self._raised_colon_error:
                self._raised_colon_error = True
                self._raise_self_response_error(
                    title='# Colon in title',
                    error_message=dedent_triple_quote_str("""
                        Titles of manuscripts in {journal_name} typically do not have a colon. '
                        Can you think of a different title that clearly state a single message without using a colon?
                        """)
                )
        if section_name == 'abstract' and section.count('\n') > 2:
            self._raise_self_response_error(
                title='# Abstract should be a single paragraph',
                error_message='The abstract should writen as a single paragraph.')
        return super()._check_and_refine_section(section, section_name)


@dataclass
class SecondTitleAbstractSectionWriterReviewGPT(FirstTitleAbstractSectionWriterReviewGPT):
    max_reviewing_rounds: int = 0
    conversation_name: str = None
    background_product_fields: Tuple[str] = ('general_dataset_description',
                                             'paper_sections:results',
                                             'literature_search:writing:background',
                                             'literature_search:writing:dataset',
                                             'literature_search:writing:results',
                                             'title_and_abstract')
    mission_prompt: str = dedent_triple_quote_str("""
        Bases on the material provided above ({actual_background_product_names}), please help me improve the \t
        title and abstract for a {journal_name} research paper. 

        {section_specific_instructions}

        I especially want you to:
        (1) Make sure that the abstract clearly states the main results of the paper \t
        (see above the {paper_sections:results}).
        (2) Make sure that the abstract correctly defines the literature gap/question/motivation \t
        (see above Literature Searches for list of related papers).

        {latex_instructions}
        Your response should be formatted as {your_response_should_be_formatted_as}
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
    section_specific_instructions: str = dedent_triple_quote_str("""\n
        The introduction should be interesting and pique your reader’s interest. 
        It should be written while citing relevant papers from the Literature Searches above.

        Specifically, the introduction should follow the following multi-paragraph structure:

        * Introduce the topic of the paper and why it is important \t
        (cite relevant papers from the above "{literature_search:writing:background}"). 

        * Explain what was already done and known on the topic, and what is then the research gap/question \t
        (cite relevant papers from the above "{literature_search:writing:results}"). If there is only a minor gap, \t
        you can use language such as "Yet, it is still unclear ...", "However, less is known about ...", \t
        etc.

        * State how the current paper addresses this gap/question \t
        (cite relevant papers from the above "{literature_search:writing:dataset}" and \t
        "{literature_search:writing:results}").

        * Outline the methodological procedure and briefly state the main findings \t
        (cite relevant papers from the above "{literature_search:writing:methods}")

        Note: each of these paragraphs should be 5-6 sentence long. Do not just write short paragraphs with less \t
        than 5 sentences!  

        Citations should be added in the following format: \\cite{paper_id}.
        Do not add a \\section{References} section, I will add it later manually.

        Note that it is not advisable to write about limitations, implications, or impact in the introduction.
        """)
    section_review_specific_instructions: str = dedent_triple_quote_str("""\n
        Also, please suggest if you see any specific additional citations that are adequate to include \t
        (from the Literature Searches above).
        """)


@dataclass
class MethodsSectionWriterReviewGPT(SectionWriterReviewBackgroundProductsConverser):
    background_product_fields: Tuple[str, ...] = ('data_file_descriptions_no_headers', 'research_goal',
                                                  'codes:data_preprocessing',
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
        The Methods section should be enclosed within triple-backtick "latex" block \
        and have 3 subsections, as follows: 

        ```latex
        \\section{Methods}

        \\subsection{Data Source}
        - Describe our data sources (see above "{data_file_descriptions}")

        \\subsection{Data Preprocessing}
        - Describe preprocessing of the data done by the Python code (see above "{codes:data_analysis}").
        - Do not include preprocessing steps that were not performed by the code. 
        - Do not include preprocessing steps that were performed by the code, but were not used as basis \t
        for further analysis affecting the result output.

        \\subsection{Data Analysis}
        - Describe each of the specific analysis steps performed by the Python code to yield the results.
        - Do not be over technical.
        - Do not enumerate the steps as a list; instead, describe the steps in a narrative form.
        ```

        Throughout the Methods section, do NOT include any of the following:
        - Missing steps not done by the code.
        - Specific version of software packages, file names, column names.
        - Names of package functions (e.g., do not say "We used sklearn.linear_model.LinearRegression", say instead \t
        "We used a linear regression model") 
        - URLs, links or references.""")

    latex_instructions: str = ''
    your_response_should_be_formatted_as: str = dedent_triple_quote_str("""
        a triple-backtick "latex" block, like this:
        ```latex
        \\section{Methods}
        \\subsection{Data Source}
        <your latex-formatted description of the data source here>
        \\subsection{Data Preprocessing}
        <your latex-formatted description of the data preprocessing here>
        \\subsection{Data Analysis}
        <your latex-formatted description of the data analysis here>
        ```
        """)

    section_review_specific_instructions: str = "{section_specific_instructions}"

    def _check_extracted_text_and_update_valid_result(self, extracted_text: List[str]):
        # Warn on "version = ..." :
        # e.g. "version = 1.2.3", "version 1.2.3", "Python 3.7", "Python 3.7.1"
        response = self._convert_extracted_text_to_fresh_looking_response(extracted_text)
        pattern = r'version(?:\s*=\s*|\s+)(\d+\.\d+(\.\d+)?)|Python\s+(\d+\.\d+)'
        if re.findall(pattern, response):
            self._raise_self_response_error(
                title='# Software packages',
                error_message=f'Do not mention specific version of software packages.')

        # Check subsection headings:
        pattern = r'\\subsection{([^}]*)}'
        matches = re.findall(pattern, response)
        if set(matches) != {'Data Source', 'Data Preprocessing', 'Data Analysis'}:
            self._raise_self_response_error(
                title='# Allowed subsections',
                error_message=dedent_triple_quote_str(f"""
                    The Methods section should only have the following 3 subsections: '
                    Data Source, Data Preprocessing, Data Analysis.
                    """)
            )
        return super()._check_extracted_text_and_update_valid_result(extracted_text)

    def run_and_get_valid_result(self) -> list:
        # Add code availability statement:
        response = [super().run_and_get_valid_result()[0] +
                    '\\subsection{Code Availability}\n\n'
                    'Custom code used to perform the data preprocessing and analysis, '
                    'as well as the raw code outputs, are provided in Supplementary Methods.']
        return response


@dataclass
class ResultsSectionWriterReviewGPT(SectionWriterReviewBackgroundProductsConverser):
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
        ('title_and_abstract', 'data_file_descriptions_no_headers_linked', 'codes:data_analysis',
         'latex_displayitems_linked', 'additional_results_linked')
    product_fields_from_which_response_is_extracted: Tuple[str, ...] = \
        ('data_file_descriptions_no_headers_linked', 'latex_displayitems_linked', 'additional_results_linked')
    self_products_to_other_products: Tuple[Tuple[str, str]] = (
        ('latex_displayitems_linked', 'latex_displayitems'),
        ('additional_results_linked', 'additional_results'),
        ('data_file_descriptions_no_headers_linked', 'data_file_descriptions_no_headers'),
    )
    max_reviewing_rounds: int = 1
    section_specific_instructions: str = dedent_triple_quote_str("""
        {general_result_instructions}
        {numeric_values_instructions}
        """)
    general_result_instructions: str = dedent_triple_quote_str("""\n
        Use the following guidelines when writing the Results:

        * Include 3-4 paragraphs, each typically focusing on one of the analysis and the resulting displayitems:
        You should typically have a separate paragraph describing each of the Tables/Figures.  \t
        If two or more display items are based on the same analysis (typically a table and a figure), \t
        they should be discussed in the same paragraph. \t
        In each such paragraph, indicate the motivation/question for the analysis, the methodology, \t
        and only then describe the results. \t
        You should describe what we see and learn from each Table/Figure. \t
        You should refer to the Tables/Figures by their labels \t
        (using \\ref{table:xxx}, \\ref{figure:xxx}), \t
        but do not add the displayitems themselves (they will be added later automatically).

        * Story-like flow: 
        It is often nice to have a story-like flow between the paragraphs, so that the reader \t
        can follow the analysis process with emphasis on the reasoning/motivation behind each analysis step. 
        For example, the first sentence of each paragraph can be a story-guiding sentences like: 
        "First, to understand whether xxx, we conducted a simple analysis of ..."; "Then, to test yyy, we performed a \t
        ..."; "Finally, to further verify the effect of zzz, we tested whether ...".

        * Conclude with a summary of the results:
        You can summarize the results at the end, with a sentence like: "In summary, these results show ...", \t
        or "Taken together, these results suggest ...".
        IMPORTANT NOTE: Your summary SHOULD NOT include a discussion of conclusions, implications, limitations, \t
        or of future work. \t
        (These will be added later as part the Discussion section, not the Results section).
        """)
    numeric_values_instructions: str = dedent_triple_quote_str("""
        * Numeric values:

        - Sources: 
        You can extract numeric values from the above provided sources: "{latex_displayitems_linked}", \t
        "{additional_results_linked}", and "{data_file_descriptions_no_headers_linked}".
        All numeric values in these sources have a \\hypertarget with a unique label. 

        - Cited numeric values should be formatted as \\hyperlink{<label>}{<value>}:
        Any numeric value extracted from the above sources should be written with a proper \\hyperlink to its \t
        corresponding source \\hypertarget.

        - Dependent values should be calculated using the \\num command.
        In scientific writing, we often need to report values which are not explicitly provided in the sources, \t
        but can rather be derived from them. For example: changing units, \t
        calculating differences, transforming regression coefficients into odds ratios, etc (see examples below).

        To derive such dependent values, please use the \\num{<formula>, "explanation"} command. 
        The <formula> contains a calculation, which will be automatically replaced with its result upon pdf compilation. 
        The "explanation" is a short textual explanation of the calculation \t
        (it will not be displayed directly in the text, but will be useful for review and traceability).  

        - Toy example for citing and calculating numeric values:

        Suppose our provided source data includes:
        ```
        No-treatment response: \\hypertarget{Z1a}{0.65} 
        With-treatment response: \\hypertarget{Z2a}{0.87}

        Treatment regression: 
        coef = \\hypertarget{Z3a}{0.17}, STD = \\hypertarget{Z3b}{0.072}, pvalue = <\\hypertarget{Z3c}{1e-6}
        ```

        Then, here are some examples of proper ways to report these provided source values:
        ```
        The no-treatment control group had a response of \\hyperlink{Z1a}{0.65} while the with-treatment \t
        group had a response of \\hyperlink{Z2a}{0.87}.

        The regression coefficient for the treatment was \\hyperlink{Z3a}{0.17} with a standard deviation of \t
        \\hyperlink{Z3b}{0.072} (P-value: < \\hyperlink{Z3c}{1e-6}).
        ```

        And here are some examples of proper ways to calculate dependent values, using the \\num command:
        ```
        The difference in response was \\num{\\hyperlink{Z2a}{0.87} - \\hyperlink{Z1a}{0.65}, \t
        "Difference between responses with and without treatment"}.

        The treatment odds ratio was \t
        \\num{exp(\\hyperlink{Z3a}{0.17}), \t
        "Translating the treatment regression coefficient to odds ratio"} (CI: \t
        \\num{exp(\\hyperlink{Z3a}{0.17} - 1.96 * \\hyperlink{Z3b}{0.072}), \t
        "low CI for treatment odds ratio, assuming normality"}, \t
        \\num{exp(\\hyperlink{Z3a}{0.17} + 1.96 * \\hyperlink{Z3b}{0.072}), \t
        "high CI for treatment odds ratio, assuming normality"}).
        ```

        * Accuracy: 
        Make sure that you are only mentioning details that are explicitly found within the Tables, Figures and \t
        Numerical Values.

        * Unknown values:
        If we need to include a numeric value that is not explicitly given in the \t
        Tables/Figures or "{additional_results_linked}", and cannot be derived from them using the \\num command, \t
        then indicate `[unknown]` instead of the numeric value. 

        For example:
        ```
        The no-treatment response was \\hyperlink{Z1a}{0.65} (STD: [unknown]).
        ```
        """)
    other_mission_prompt: str = dedent_triple_quote_str("""
        Based on the material provided above, please write the Results section for a {journal_name} research paper.

        {general_result_instructions}

        * You can use the \\num command to calculate dependent values from the provided numeric values \t
        (they will be automatically replaced with the actual numeric values in compilation).
        """)
    section_review_specific_instructions: str = dedent_triple_quote_str("""
        Do not suggest adding missing information, or stating whats missing from the displayitems or Numerical Values.
        Only suggest changes that are relevant to the Results section itself and that are supported by the given \t
        displayitems and Numerical Values.

        Do not suggest changes to the {goal_noun} that may require data not available in the the \t
        displayitems and Numerical Values.
        """)
    sentence_to_add_at_the_end_of_reviewer_response: str = dedent_triple_quote_str("""\n\n
        Please correct your response according to any points in my feedback that you find relevant and applicable.
        Send back a complete rewrite of the {pretty_section_names}.
        Make sure to send the full corrected {pretty_section_names}, not just the parts that were revised.
        Remember to include the numeric values in the format \\hyperlink{<label>}{<value>} and use the \\num command \t
        for dependent values.
    """)

    def _get_displayitem_labels(self, section_name: str) -> List[str]:
        return [get_displayitem_label(displayitem)
                for displayitem in self.products.get_latex_displayitems()[section_name]]

    def _check_and_refine_section(self, section: str, section_name: str) -> str:
        result = super()._check_and_refine_section(section, section_name)
        displayitems_labels = self._get_displayitem_labels(section_name)
        figure_or_table = 'Figure' if section_name.startswith('figure') else 'Table'
        for displayitem_label in displayitems_labels:
            if displayitem_label not in section:
                self._raise_self_response_error(
                    title='# Missing Displayitem reference',
                    error_message=dedent_triple_quote_str(f"""
                        The {section_name} section should specifically reference each of the Displayitems that we have.
                        Please make sure we have a sentence addressing {figure_or_table} "{displayitem_label}".
                        The sentence should have a reference: "{figure_or_table}~\\ref{{{displayitem_label}}}".
                        """)
                )
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
    section_review_specific_instructions: str = dedent_triple_quote_str("""\n
        Also, please suggest if you see any specific additional citations that are adequate to include \t
        (from the Literature Searches above).
        """)
    section_specific_instructions: str = dedent_triple_quote_str("""\n
        The Discussion section should follow the following structure:
        * Recap the subject of the study (cite relevant papers from the above "{literature_search:writing:background}").  
        * Recap our methodology (see "Methods" section above) and the main results \t
        (see "{paper_sections:results}" above), \t
        and compare them to the results from prior literature (see above "{literature_search:writing:results}"). 
        * Discuss the limitations of the study.
        * End with a concluding paragraph summarizing the main results, their implications and impact, \t
        and future directions.

        Citations should be added in the following format: \\cite{paper_id}.
        Do not add a \\section{References} section, I will add it later manually.
        """)
