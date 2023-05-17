from dataclasses import dataclass, field
from typing import Optional

from scientistgpt.base_steps.base_steps_runner import BaseStepsRunner
from scientistgpt.base_steps.request_products_from_user import DirectorProductGPT

from .cast import ScientificAgent
from .add_citations import AddCitationReviewGPT
from .coding_steps import ScientificCodeProductsGPT
from .get_template import get_paper_template_path
from .produce_pdf_step import ProduceScientificPaperPDFWithAppendix
from .scientific_products import ScientificProducts
from .scientific_stage import ScientificStage
from .reviewing_steps import GoalReviewGPT, PlanReviewGPT, \
    ResultsInterpretationReviewGPT, PaperSectionReviewGPT, TitleAbstractReviewGPT, PaperSectionWithTablesReviewGPT

PAPER_TEMPLATE_FILE: str = get_paper_template_path('standard_paper.tex')
SECTIONS_TO_ADD_CITATIONS_TO = ['introduction', 'discussion']
SECTIONS_TO_ADD_TABLES_TO = ['results']


@dataclass
class ScientificStepsRunner(BaseStepsRunner):

    cast = ScientificAgent
    products: ScientificProducts = field(default_factory=ScientificProducts)
    research_goal: Optional[str] = None

    def _run_all_steps(self) -> ScientificProducts:

        products = self.products  # Start with empty products

        # Get the paper section names:
        paper_producer = ProduceScientificPaperPDFWithAppendix.from_(
            self,
            paper_template_filepath=PAPER_TEMPLATE_FILE,
            output_filename='paper.pdf',
        )
        paper_section_names = paper_producer.get_paper_section_names()

        # Data file descriptions:
        director_converser = DirectorProductGPT.from_(self,
                                                      assistant_agent=ScientificAgent.Director,
                                                      user_agent=ScientificAgent.Performer,
                                                      conversation_name='with_director',
                                                      )
        self.advance_stage_and_set_active_conversation(ScientificStage.DATA, ScientificAgent.Director)
        products.data_file_descriptions = director_converser.get_product_or_no_product_from_director(
            product_field='data_file_descriptions', returned_product=self.data_file_descriptions)
        self.send_product_to_client('data_file_descriptions')

        # Goal
        self.advance_stage_and_set_active_conversation(ScientificStage.GOAL, ScientificAgent.Director)
        products.research_goal = director_converser.get_product_or_no_product_from_director(
            product_field='research_goal', returned_product=self.research_goal,
            acknowledge_no_product_message="OK. no problem. I will devise the goal myself.")
        if products.research_goal is None:
            # we did not get a goal from the director, so we need to devise it ourselves:
            self.set_active_conversation(ScientificAgent.GoalReviewer)
            products.research_goal = GoalReviewGPT.from_(self).initialize_and_run_dialog()
        self.send_product_to_client('research_goal')

        # Analysis plan
        self.advance_stage_and_set_active_conversation(ScientificStage.PLAN, ScientificAgent.PlanReviewer)
        products.analysis_plan = PlanReviewGPT.from_(self).initialize_and_run_dialog()
        self.send_product_to_client('analysis_plan')

        # Code and output
        self.advance_stage_and_set_active_conversation(ScientificStage.CODE, ScientificAgent.Debugger)
        products.code_and_output = ScientificCodeProductsGPT.from_(self).get_analysis_code()
        self.send_product_to_client('code_and_output')

        # Results interpretation
        self.advance_stage_and_set_active_conversation(
            ScientificStage.INTERPRETATION, ScientificAgent.InterpretationReviewer)
        products.results_summary = ResultsInterpretationReviewGPT.from_(self).initialize_and_run_dialog()
        self.send_product_to_client('results_summary')

        # Paper sections
        self.advance_stage_and_set_active_conversation(ScientificStage.WRITING, ScientificAgent.Writer)
        title_and_abstract_names = ['title', 'abstract']
        products.paper_sections['title'], products.paper_sections['abstract'] = \
            TitleAbstractReviewGPT.from_(self, section_names=title_and_abstract_names).get_sections()

        for section_name in paper_section_names:
            if section_name not in title_and_abstract_names:
                products.paper_sections[section_name] = \
                    PaperSectionReviewGPT.from_(self, section_names=[section_name]).get_section()
        self.send_product_to_client('paper_sections')

        # Add citations to relevant paper sections
        self.advance_stage_and_set_active_conversation(ScientificStage.CITATIONS, ScientificAgent.CitationExpert)
        for section_name in SECTIONS_TO_ADD_CITATIONS_TO:
            products.cited_paper_sections[section_name] = \
                AddCitationReviewGPT.from_(self, section_name=section_name).rewrite_section_with_citations()
        self.send_product_to_client('cited_paper_sections')

        # Add tables to results section
        self.advance_stage_and_set_active_conversation(ScientificStage.TABLES, ScientificAgent.TableExpert)
        for section_name in SECTIONS_TO_ADD_TABLES_TO:
            products.tabled_paper_sections[section_name] = \
                PaperSectionWithTablesReviewGPT.from_(self, section_names=[section_name]).get_section()
        self.send_product_to_client('tabled_paper_sections')

        paper_producer.assemble_compile_paper()

        return products
