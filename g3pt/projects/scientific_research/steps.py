from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Union

from pygments import highlight
from pygments.formatters.latex import LatexFormatter
from pygments.lexers import PythonLexer

from g3pt.base_steps.base_latex_to_pdf import BaseLatexToPDF, BaseLatexToPDFWithAppendix
from g3pt.base_steps.write_code import BaseCodeProductsGPT
from g3pt.projects.scientific_research.cast import ScientificAgent
from g3pt.projects.scientific_research.scientific_products import ScientificProducts, \
    get_from_most_updated_paper_sections
from g3pt.utils.citataion_utils import remove_citations_from_section

from g3pt.base_steps.base_products_conversers import BaseProductsQuotedReviewGPT, \
    BaseProductsReviewGPT
from g3pt.latex import extract_latex_section_from_response, FailedToExtractLatexContent
from g3pt.utils import dedent_triple_quote_str
from g3pt.utils.replacer import with_attribute_replacement
from g3pt.utils.text_utils import nicely_join, NiceList, wrap_python_code

sentence_to_add_at_the_end_of_reviewee_response = dedent_triple_quote_str("""\n
    Please provide feedback on the above {goal_noun}, with specific attention to whether it can be \
    studied using only the provided dataset, without requiring any additional data \
    (pay attention to using only data explicitly available in the provided headers of the our data files \
    as described in our dataset, above).
    Do not suggest changes to the {goal_noun} that may require data not available in our dataset.
    """)


@dataclass
class GoalReviewGPT(BaseProductsQuotedReviewGPT):
    background_product_fields = ['data_file_descriptions']
    conversation_name: str = 'research_goal'
    other_conversation_name: str = 'research_goal_reviewer'
    goal_noun: str = 'research goal'
    goal_verb: str = 'suggest'
    assistant_agent: ScientificAgent = ScientificAgent.PlanReviewer
    user_agent: ScientificAgent = ScientificAgent.Student
    termination_phrase: str = \
        'I hereby approve that the research goal is well-defined and can be studied using only the provided dataset'
    user_initiation_prompt: str = dedent_triple_quote_str("""
        Please {goal_verb} a {goal_noun}. Please do not include suggested methodology, just the research goal.
        Make sure you suggest a research goal that can be studied using only the provided dataset, without requiring \
        any additional data \
        (pay attention to using only data available based on the provided headers of the our data files \
        as in the description of our dataset, above).
        """)
    other_system_prompt: str = dedent_triple_quote_str("""
        You are a {reviewer} for a {reviewee} who needs to {goal_verb} a {goal_noun}.
        Your job is to advise me, the {reviewee}, and provide a constructive bullet-point feedback in repeated cycles \
        of improvements and feedback.

        Pay special attention to whether the research goal can be achieved using only the provided dataset (without \
        requiring additional data).

        When you feel that the provided research goal is interesting and can be achieved without requiring \
        additional data except the provided dataset, respond explicitly with: 
        "{termination_phrase}" (termination-phrase).
        If you feel that the initial goal description that I send you is already interesting, well defined, \
        and fits the provided data, it is perfectly fine and encouraged to respond with with termination-phrase \
        immediately, without requesting any improvement cycles.
        """)
    sentence_to_add_at_the_end_of_reviewee_response: str = sentence_to_add_at_the_end_of_reviewee_response


@dataclass
class PlanReviewGPT(BaseProductsQuotedReviewGPT):
    max_rounds: int = 0  # no review cycles
    background_product_fields = ['data_file_descriptions', 'research_goal']
    conversation_name: str = 'analysis_plan'
    goal_noun: str = 'short data analysis plan'
    goal_verb: str = 'write'
    assistant_agent: ScientificAgent = ScientificAgent.PlanReviewer
    user_agent: ScientificAgent = ScientificAgent.Student
    sentence_to_add_at_the_end_of_reviewee_response: str = sentence_to_add_at_the_end_of_reviewee_response


@dataclass
class ResultsInterpretationReviewGPT(BaseProductsQuotedReviewGPT):
    max_rounds: int = 1
    background_product_fields = ['data_file_descriptions', 'research_goal', 'code_and_output']
    conversation_name: str = 'results_interpretation'
    goal_noun: str = 'description and interpretation of the results'
    goal_verb: str = 'write'
    assistant_agent: ScientificAgent = ScientificAgent.PlanReviewer
    user_agent: ScientificAgent = ScientificAgent.Student
    sentence_to_add_at_the_end_of_reviewee_response: str = dedent_triple_quote_str("""
        Please provide feedback on the above {goal_noun}, with specific attention to whether this description \
        is fully supported by our data (pay specific attention to the output of our analysis code, above).
    """)


@dataclass
class BaseWriterReviewGPT(BaseProductsReviewGPT):
    """
    Base class for the writer of a paper section in latex format.
    """
    max_rounds: int = 3
    goal_noun: str = None
    conversation_name: str = None
    goal_verb: str = 'write'
    reviewee: str = 'scientific writer'
    reviewer: str = 'scientific reviewer'
    assistant_agent: ScientificAgent = ScientificAgent.Writer
    user_agent: ScientificAgent = ScientificAgent.Student
    section_names: Optional[Union[str, list[str]]] = None
    section_contents: Union[str, List[str]] = field(default_factory=list)

    def __post_init__(self):
        self.goal_noun = self.goal_noun or nicely_join(self.section_names)
        self.conversation_name = self.conversation_name or self.goal_noun.replace(' ', '_')
        super().__post_init__()

    system_prompt: str = dedent_triple_quote_str("""
        You are a scientist capable of writing full-length, scientifically sound research papers.

        You should:
        1. Write every part of the paper in scientific language, in `.tex` format.
        2. Write the paper section by section.
        3. Write the paper in a way that is consistent with the scientific products provided to you.
        4. Do not cite any papers.
        """)

    user_initiation_prompt: str = dedent_triple_quote_str(r"""
        Based on the material provided above (research goal, analysis plan, and results description), please {goal_verb} 
        only the {goal_noun} of a scientific paper. Do not write any other parts!
        Write in tex format including the proper latex commands, any math or symbols that needs tex escapes.
        """)

    other_system_prompt: str = dedent_triple_quote_str("""
        You are a {reviewer} for a {reviewee} who needs to {goal_verb} a {goal_noun} for a scientific paper.
        Your job is to advise me, the {reviewee}, and provide constructive bullet-point feedback in repeated cycles \
        of improvements and feedback.

        When you feel that the goal has been achieved, respond explicitly with:
         "{termination_phrase}" (termination-phase).
    """)

    sentence_to_add_at_the_end_of_reviewer_response: str = dedent_triple_quote_str("""
        Please correct your response according to my feedback and send back a complete rewrite of the {goal_noun}.
        Make sure to send the full corrected {goal_noun}, not just the parts that were revised.
    """)

    sentence_to_add_at_the_end_of_reviewee_response: str = \
        "Please provide constructive feedback on the above {goal_noun}"

    def _check_self_response(self, response: str, section_names=None) -> Optional[str]:
        """
        Check that the response is a valid latex section
        """
        try:
            self.section_contents = []
            for section_name in self.section_names:
                extracted_section = extract_latex_section_from_response(response, section_name)
                extracted_section_without_references = remove_citations_from_section(extracted_section)
                self.section_contents.append(extracted_section_without_references)
        except FailedToExtractLatexContent as e:
            error_message = dedent_triple_quote_str("""
                {}

                Please rewrite the {} part again with the correct latex formatting.
                """).format(e, self.goal_noun)
            return error_message
        return None

    @with_attribute_replacement
    def get_sections(self) -> Union[str, list[str]]:
        self.initialize_and_run_dialog()
        return self.section_contents


@dataclass
class TitleAbstractReviewGPT(BaseWriterReviewGPT):
    max_rounds: int = 2
    background_product_fields = ['data_file_descriptions', 'research_goal', 'analysis_plan', 'results_summary']
    user_initiation_prompt: str = dedent_triple_quote_str(r"""
        Based on the material provided above (research goal, analysis plan, and results description), please {goal_verb} 
        only the {goal_noun} of a scientific paper. Do not write any other parts!
        Write in tex format including the \\title{{}} and \\begin{{abstract}} ... \\end{{abstract}} commands, 
        and any math or symbols that needs tex escapes.
    """)


@dataclass
class PaperSectionReviewGPT(BaseWriterReviewGPT):
    section_name: str = None
    max_rounds: int = 1
    background_product_fields = ['data_file_descriptions', 'research_goal', 'analysis_plan', 'results_summary',
                                 'title_and_abstract']
    user_initiation_prompt: str = dedent_triple_quote_str(r"""
        Based on the material provided above (research goal, analysis plan, and results description), please {goal_verb} 
        only the {goal_noun} of a scientific paper. Do not write any other parts!
        Write in tex format including the \\section{{}} command, and any math or symbols that needs tex escapes.
    """)

    def __post_init__(self):
        self.section_names = [self.section_name]
        super().__post_init__()

    @with_attribute_replacement
    def get_section(self):
        return self.get_sections()[0]


@dataclass
class PaperSectionWithTablesReviewGPT(PaperSectionReviewGPT):
    goal_noun: str = '{section_name} section with tables'
    goal_verb: str = 'rewrite'
    background_product_fields = ['results_summary', 'code_and_output',
                                 'title_and_abstract']
    max_rounds: int = 0
    user_initiation_prompt: str = dedent_triple_quote_str(r"""
        Based on the material provided above (research goal, results description, and outputs), please {goal_verb} \
        only the {goal_noun}.
        Usually in scientific papers include one or two tables summarizing the main findings.
        The tables should include information that was only extracted from the information provided.
        Add the tables centered in booktabs, multirow format with caption and label. 
        In addition, change the results section text to refer to the tables (use their labels if necessary),
        to incorporate them as integral part of the {section_name} section. Do not add figures, only tables.
        Write in tex format including \\section{{}} command, any math or symbols that needs tex escapes.
    """)

    def _get_background_product_fields(self):
        return self.background_product_fields + ['most_updated_paper_sections_' + self.section_name]


@dataclass
class ScientificCodeProductsGPT(BaseCodeProductsGPT):
    products: ScientificProducts = None
    background_product_fields = ['data_file_descriptions', 'research_goal', 'analysis_plan']
    conversation_name: str = 'code_debugging'
    assistant_agent: ScientificAgent = ScientificAgent.Debugger
    user_agent: ScientificAgent = ScientificAgent.Student
    code_requesting_prompt: str = BaseCodeProductsGPT.code_requesting_prompt + dedent_triple_quote_str("""
        All results we may need for a scientific paper should be saved to that file, including \
        analysis findings, summary statistics, etc. 
        Do not write to any other files and do not plot anything to screen.
        """)
    requesting_code_explanation_prompt: str = dedent_triple_quote_str("""
        Please explain what your code does. Do not provide a line-by-line explanation, rather provide a \
        high-level explanation of the code in a language suitable for a Methods section of a research \
        paper. Also explain what does the code writes into the {{}} file.
        """)

    @property
    def data_filenames(self) -> NiceList[str]:
        return NiceList(self.products.data_file_descriptions.get_data_filenames(),
                        wrap_with='"',
                        prefix='{} data file[s]: ')

    @property
    def data_folder(self) -> Optional[Path]:
        return Path(self.products.data_file_descriptions.data_folder)


@dataclass
class ProduceScientificPaperPDF(BaseLatexToPDF):
    products: ScientificProducts = None

    def _choose_sections_to_add_to_paper_and_collect_references(self):
        """
        Chooses what sections to add to the paper.
        Start by choosing section with tables, then cited sections, then without both of those.
        If there are references we also collect them to a set.
        """
        references = set()
        sections = {}
        for section_name in self.get_paper_section_names():
            sections[section_name] = get_from_most_updated_paper_sections(self.products, section_name)
            if section_name in self.products.cited_paper_sections:
                references |= self.products.cited_paper_sections[section_name][1]  # 1 is the references set

        return sections, references


@dataclass
class ProduceScientificPaperPDFWithAppendix(BaseLatexToPDFWithAppendix, ProduceScientificPaperPDF):
    latex_formatter: LatexFormatter = LatexFormatter(linenos=True, texcomments=True, mathescape=True)

    def _choose_sections_to_add_to_paper_and_collect_references(self):
        """
        Chooses what sections to add to the paper.
        Start by choosing section with tables, then cited sections, then without both of those.
        If there are references we also collect them to a set.
        """
        sections, references = super()._choose_sections_to_add_to_paper_and_collect_references()
        sections['appendix'] = self._create_appendix()
        sections['preamble'] = self.preamble
        return sections, references

    def _create_code_section(self):
        """
        Create the code section.
        """
        code_and_output = self.products.code_and_output
        code = wrap_python_code(code_and_output.code)
        explanation = code_and_output.explanation
        latex_code = highlight(code, PythonLexer(), self.latex_formatter)
        code_section = """\\section{Python Analysis Code} \\label{sec:code} This is the analysis code that was 
        generated using ChatGPT in order to analyse the given data according to the research goal:"""
        code_section += '\n\n' + latex_code
        code_section += """
        The explanation of the code, also produced by ChatGPT:
        """
        code_section += '\n\n' + explanation
        return code_section

    def _create_data_description_section(self):
        """
        Create the data description section.
        """
        data_file_descriptions = self.products.data_file_descriptions
        data_description_section = """\\section{Data Description} \\label{sec:data_description} This is the data
        description that was provided by the user:"""
        data_description_section += '\n\n' + str(data_file_descriptions)
        return data_description_section

    @property
    def preamble(self):
        return self.latex_formatter.get_style_defs()

    def _create_appendix(self):
        """
        Create the appendix.
        """
        appendix = self._create_data_description_section()
        appendix += '\n\n' + self._create_code_section()
        return appendix
