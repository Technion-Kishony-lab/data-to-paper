from dataclasses import dataclass, field
from typing import Optional

from scientistgpt.base_steps.base_steps_runner import BaseStepsRunner
from scientistgpt.base_steps.request_products_from_user import DirectorProductGPT

from .cast import ScientificAgent
from .add_citations import AddCitationReviewGPT
from .coding_steps import DataExplorationCodeProductsGPT, DataAnalysisCodeProductsGPT, DataPreprocessingCodeProductsGPT
from .get_template import get_paper_template_path
from .produce_pdf_step import ProduceScientificPaperPDFWithAppendix
from .scientific_products import ScientificProducts
from .scientific_stage import ScientificStages
from .reviewing_steps import GoalReviewGPT, PlanReviewGPT, \
    ResultsInterpretationReviewGPT, TablesReviewGPT, KeyNumericalResultsExtractorReviewGPT
from .writing_steps import SectionWriterReviewGPT, TitleAbstractSectionWriterReviewGPT, MethodsSectionWriterReviewGPT, \
    ReferringTablesSectionWriterReviewGPT, DiscussionSectionWriterReviewGPT, ConclusionSectionWriterReviewGPT, \
    IntroductionSectionWriterReviewGPT

PAPER_TEMPLATE_FILE: str = get_paper_template_path('standard_paper.tex')
SECTIONS_TO_ADD_CITATIONS_TO = ['introduction', 'discussion']
SECTIONS_TO_ADD_TABLES_TO = ['results']


@dataclass
class ScientificStepsRunner(BaseStepsRunner):

    cast = ScientificAgent
    products: ScientificProducts = field(default_factory=ScientificProducts)
    research_goal: Optional[str] = None

    should_do_data_exploration: bool = True
    should_do_data_preprocessing: bool = False
    should_prepare_data_analysis_plan: bool = False
    should_add_citations: bool = True
    should_add_tables: bool = True
    should_interpret_results: bool = False

    number_of_tables_to_add: int = 2

    def get_sections_to_writing_class(self):
        return {
            ('title', 'abstract'): TitleAbstractSectionWriterReviewGPT,
            ('introduction', ): IntroductionSectionWriterReviewGPT,
            ('methods', ): MethodsSectionWriterReviewGPT,
            ('results', ): ReferringTablesSectionWriterReviewGPT if self.should_add_tables else SectionWriterReviewGPT,
            ('discussion', ): DiscussionSectionWriterReviewGPT,
            ('conclusion', ): ConclusionSectionWriterReviewGPT,
        }

    def assert_paper_sections_to_write_matches_template(self, template_sections, sections_to_writing_class):
        flattened_paper_sections_to_write = []
        for sections in sections_to_writing_class:
            flattened_paper_sections_to_write.extend(sections)
        assert set(flattened_paper_sections_to_write) == set(template_sections)

    def _run_all_steps(self) -> ScientificProducts:

        products = self.products  # Start with empty products

        # Get the paper section names:
        paper_producer = ProduceScientificPaperPDFWithAppendix.from_(
            self,
            paper_template_filepath=PAPER_TEMPLATE_FILE,
            output_filename='paper.pdf',
        )
        paper_section_names = paper_producer.get_paper_section_names()
        sections_to_writing_class = self.get_sections_to_writing_class()
        self.assert_paper_sections_to_write_matches_template(paper_section_names, sections_to_writing_class)

        # Data file descriptions:
        director_converser = DirectorProductGPT.from_(self,
                                                      assistant_agent=ScientificAgent.Director,
                                                      user_agent=ScientificAgent.Performer,
                                                      conversation_name='with_director',
                                                      )
        self.advance_stage_and_set_active_conversation(ScientificStages.DATA, ScientificAgent.Director)
        products.data_file_descriptions = director_converser.get_product_or_no_product_from_director(
            product_field='data_file_descriptions', returned_product=self.data_file_descriptions)
        self.send_product_to_client('data_file_descriptions')

        # Data exploration
        if self.should_do_data_exploration:
            self.advance_stage_and_set_active_conversation(ScientificStages.EXPLORATION, ScientificAgent.DataExplorer)
            products.codes_and_outputs['data_exploration'] = \
                DataExplorationCodeProductsGPT.from_(self).get_code_and_output()
            self.send_product_to_client('codes_and_outputs:data_exploration')

        # Goal
        self.advance_stage_and_set_active_conversation(ScientificStages.GOAL, ScientificAgent.Director)
        products.research_goal = director_converser.get_product_or_no_product_from_director(
            product_field='research_goal', returned_product=self.research_goal,
            acknowledge_no_product_message="OK. no problem. I will devise the goal myself.")
        if products.research_goal is None:
            # we did not get a goal from the director, so we need to devise it ourselves:
            self.set_active_conversation(ScientificAgent.GoalReviewer)
            products.research_goal = GoalReviewGPT.from_(self).initialize_and_run_dialog()
        self.send_product_to_client('research_goal')

        # Analysis plan
        if self.should_prepare_data_analysis_plan:
            self.advance_stage_and_set_active_conversation(ScientificStages.PLAN, ScientificAgent.PlanReviewer)
            products.analysis_plan = PlanReviewGPT.from_(self).initialize_and_run_dialog()
            self.send_product_to_client('analysis_plan')

        # Data Preprocessing
        if self.should_do_data_preprocessing:
            self.advance_stage_and_set_active_conversation(
                ScientificStages.PREPROCESSING, ScientificAgent.DataPreprocessor)
            products.codes_and_outputs['data_preprocessing'] = \
                DataPreprocessingCodeProductsGPT.from_(self).get_code_and_output()
            self.send_product_to_client('codes_and_outputs:data_preprocessing')

        # Analysis code and output
        self.advance_stage_and_set_active_conversation(ScientificStages.CODE, ScientificAgent.Debugger)
        products.codes_and_outputs['data_analysis'] = \
            DataAnalysisCodeProductsGPT.from_(self).get_code_and_output()
        self.send_product_to_client('codes_and_outputs:data_analysis')

        self.advance_stage_and_set_active_conversation(ScientificStages.INTERPRETATION,
                                                       ScientificAgent.InterpretationReviewer)
        # Tables
        if self.should_add_tables:
            products.tables['results'] = []
            for i in range(self.number_of_tables_to_add):
                table = TablesReviewGPT.from_(
                    self, section_names=['table'], table_number=i + 1, conversation_name=f'table_{i + 1}',
                    total_number_of_tables=self.number_of_tables_to_add).get_section()
                products.tables['results'].append(table)

        # Numerical results
        products.numeric_values = KeyNumericalResultsExtractorReviewGPT.from_(self).run_dialog_and_get_python_value()
        self.send_product_to_client('tables_and_numeric_values')

        # Results interpretation
        if self.should_interpret_results:
            self.advance_stage_and_set_active_conversation(
                ScientificStages.INTERPRETATION, ScientificAgent.InterpretationReviewer)
            products.results_summary = ResultsInterpretationReviewGPT.from_(self).initialize_and_run_dialog()
            self.send_product_to_client('results_summary')

        # Paper sections
        self.advance_stage_and_set_active_conversation(ScientificStages.WRITING, ScientificAgent.Writer)
        for section_names, writing_class in sections_to_writing_class.items():
            sections = writing_class.from_(self, section_names=section_names).get_sections()
            for section_name, section in zip(section_names, sections):
                products.paper_sections[section_name] = section
        self.send_product_to_client('paper_sections')

        # Add citations to relevant paper sections
        if self.should_add_citations:
            self.advance_stage_and_set_active_conversation(ScientificStages.CITATIONS, ScientificAgent.CitationExpert)
            for section_name in SECTIONS_TO_ADD_CITATIONS_TO:
                products.cited_paper_sections_and_citations[section_name] = \
                    AddCitationReviewGPT.from_(self, section_name=section_name,
                                               conversation_name=f'add_citations_to_{section_name}')\
                        .rewrite_section_with_citations()
            self.send_product_to_client('cited_paper_sections_and_citations')

        paper_producer.assemble_compile_paper()

        return products
