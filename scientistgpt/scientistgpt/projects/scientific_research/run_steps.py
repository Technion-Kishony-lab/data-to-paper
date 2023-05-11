from dataclasses import dataclass, field
from typing import Optional

from scientistgpt.base_steps.base_steps_runner import BaseStepsRunner
from scientistgpt.base_steps.request_products_from_user import DirectorProductGPT

from .cast import ScientificAgent
from .add_citations import AddCitationReviewGPT
from .get_template import get_paper_template_path
from .scientific_products import ScientificProducts
from .scientific_stage import ScientificStage
from .steps import GoalReviewGPT, PlanReviewGPT, \
    ResultsInterpretationReviewGPT, PaperSectionReviewGPT, TitleAbstractReviewGPT, PaperSectionWithTablesReviewGPT, \
    ScientificCodeProductsGPT, ProduceScientificPaperPDFWithAppendix

PAPER_TEMPLATE_FILE: str = get_paper_template_path('standard_paper.tex')
SECTIONS_TO_ADD_CITATIONS_TO = ['introduction', 'discussion']
SECTIONS_TO_ADD_TABLES_TO = ['results']


@dataclass
class ScientificStepsRunner(BaseStepsRunner):

    cast = ScientificAgent
    products: ScientificProducts = field(default_factory=ScientificProducts)
    research_goal: Optional[str] = None

    def _run_all_steps(self) -> ScientificProducts:
        # Prepare empty products
        products = self.products
        paper_producer = ProduceScientificPaperPDFWithAppendix(
            paper_template_filepath=PAPER_TEMPLATE_FILE,
            products=products,
            output_file_path=self.output_directory / 'paper.pdf',
        )
        paper_section_names = paper_producer.get_paper_section_names()

        # Data file descriptions:
        director_converser = self._get_converser(DirectorProductGPT,
                                                 assistant_agent=ScientificAgent.Director,
                                                 user_agent=ScientificAgent.Performer,
                                                 conversation_name='with_director',
                                                 )
        self.advance_stage_and_set_active_conversation(ScientificStage.DATA, ScientificAgent.Director)
        products.data_file_descriptions = director_converser.get_product_or_no_product_from_director(
            product_field='data_file_descriptions', returned_product=self.data_file_descriptions)

        # Goal
        self.advance_stage_and_set_active_conversation(ScientificStage.GOAL, ScientificAgent.Director)
        products.research_goal = director_converser.get_product_or_no_product_from_director(
            product_field='research_goal', returned_product=self.research_goal,
            acknowledge_no_product_message="OK. no problem. I will devise the goal myself.")
        if products.research_goal is None:
            # we did not get a goal from the director, so we need to devise it ourselves:
            self.set_active_conversation(self.get_conversation_name_for_agent(ScientificAgent.Director))
            products.research_goal = self._get_converser(GoalReviewGPT).initialize_and_run_dialog()

        # Analysis plan
        self.advance_stage_and_set_active_conversation(ScientificStage.PLAN, ScientificAgent.PlanReviewer)
        products.analysis_plan = self._get_converser(PlanReviewGPT).initialize_and_run_dialog()

        # Code and output
        self.advance_stage_and_set_active_conversation(ScientificStage.CODE, ScientificAgent.Debugger)
        products.code_and_output = self._get_converser(ScientificCodeProductsGPT).get_analysis_code()

        # Results interpretation
        self.advance_stage_and_set_active_conversation(
            ScientificStage.INTERPRETATION, ScientificAgent.InterpretationReviewer)
        products.results_summary = self._get_converser(ResultsInterpretationReviewGPT).initialize_and_run_dialog()

        # Paper sections
        self.advance_stage_and_set_active_conversation(ScientificStage.WRITING, ScientificAgent.Writer)
        title_and_abstract_names = ['title', 'abstract']
        products.paper_sections['title'], products.paper_sections['abstract'] = \
            self._get_converser(TitleAbstractReviewGPT, section_names=title_and_abstract_names).get_sections()

        for section_name in paper_section_names:
            if section_name not in title_and_abstract_names:
                products.paper_sections[section_name] = \
                    self._get_converser(PaperSectionReviewGPT, section_name=section_name).get_section()

        # Add citations to relevant paper sections
        self.advance_stage_and_set_active_conversation(ScientificStage.CITATIONS, ScientificAgent.CitationExpert)
        for section_name in SECTIONS_TO_ADD_CITATIONS_TO:
            products.cited_paper_sections[section_name] = \
                self._get_converser(AddCitationReviewGPT, section_name=section_name).rewrite_section_with_citations()

        # Add tables to results section
        self.advance_stage_and_set_active_conversation(ScientificStage.TABLES, ScientificAgent.TableExpert)
        for section_name in SECTIONS_TO_ADD_TABLES_TO:
            products.paper_sections_with_tables[section_name] = \
                self._get_converser(PaperSectionWithTablesReviewGPT, section_name=section_name).get_section()

        paper_producer.assemble_compile_paper()
        self.advance_stage(ScientificStage.FINISHED)

        return products
