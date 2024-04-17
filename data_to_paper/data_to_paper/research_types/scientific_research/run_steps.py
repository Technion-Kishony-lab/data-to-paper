from dataclasses import dataclass, field
from typing import Optional, Tuple, Type, List, Union

from data_to_paper.base_steps import BaseStepsRunner, DirectorProductGPT, CheckLatexCompilation

from .cast import ScientificAgent
from .add_citations import AddCitationReviewGPT
from .coding.after_coding import RequestCodeExplanation, RequestCodeProducts
from .coding.latex_tables import CreateLatexTablesCodeProductsGPT
from .coding.preprocessing import DataPreprocessingCodeProductsGPT
from .coding.data_analysis import DataAnalysisCodeProductsGPT
from .coding.data_exploration import DataExplorationCodeProductsGPT
from .literature_search import WritingLiteratureSearchReviewGPT, GoalLiteratureSearchReviewGPT
from .produce_pdf_step import ProduceScientificPaperPDFWithAppendix
from .scientific_products import ScientificProducts
from .scientific_stage import ScientificStages, SECTION_NAMES_TO_WRITING_STAGES
from .reviewing_steps import GoalReviewGPT, HypothesesTestingPlanReviewGPT, NoveltyAssessmentReview, ReGoalReviewGPT, \
    GetMostSimilarCitations
from .writing_steps import SectionWriterReviewBackgroundProductsConverser, \
    FirstTitleAbstractSectionWriterReviewGPT, SecondTitleAbstractSectionWriterReviewGPT, \
    MethodsSectionWriterReviewGPT, IntroductionSectionWriterReviewGPT, ResultsSectionWriterReviewGPT, \
    DiscussionSectionWriterReviewGPT

PAPER_SECTIONS_NAMES = ['title', 'abstract', 'introduction', 'results', 'discussion', 'methods']
SECTIONS_WITH_CITATIONS = ['introduction', 'discussion']

SECTIONS_TO_WRITING_CLASS = [
            (('results',), ResultsSectionWriterReviewGPT),
            (('title', 'abstract'), SecondTitleAbstractSectionWriterReviewGPT),
            (('methods',), MethodsSectionWriterReviewGPT),
            (('introduction',), IntroductionSectionWriterReviewGPT),
            (('discussion',), DiscussionSectionWriterReviewGPT),
            # (('conclusion',), ConclusionSectionWriterReviewGPT),
        ]


@dataclass
class ScientificStepsRunner(BaseStepsRunner, CheckLatexCompilation):

    cast = ScientificAgent
    products: ScientificProducts = field(default_factory=ScientificProducts)
    research_goal: Optional[str] = None
    project_specific_goal_guidelines: str = ""
    max_goal_refinement_iterations: int = 3

    should_do_data_exploration: bool = True
    should_do_data_preprocessing: bool = False
    should_prepare_hypothesis_testing_plan: bool = True
    should_do_literature_search: bool = True

    excluded_citation_titles: List[str] = None,  # Title of papers that we don't allow to be cited

    def get_sections_to_writing_class(
            self) -> List[Tuple[Union[str, Tuple[str, ...]], Type[SectionWriterReviewBackgroundProductsConverser]]]:
        return SECTIONS_TO_WRITING_CLASS

    def assert_paper_sections_to_write_matches_template(self, template_sections, sections_to_writing_class):
        flattened_paper_sections_to_write = []
        for sections, _ in sections_to_writing_class:
            flattened_paper_sections_to_write.extend(sections)
        assert set(flattened_paper_sections_to_write) == set(template_sections)

    def _run_all_steps(self) -> ScientificProducts:

        products = self.products  # Start with empty products

        # Set the paper section names:
        sections_and_writing_class = self.get_sections_to_writing_class()
        self.assert_paper_sections_to_write_matches_template(PAPER_SECTIONS_NAMES,
                                                             sections_and_writing_class)
        paper_producer = ProduceScientificPaperPDFWithAppendix.from_(
            self,
            latex_document=self.latex_document,
            output_filename='paper.pdf',
            paper_section_names=PAPER_SECTIONS_NAMES,
        )

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
            RequestCodeProducts.from_(self,
                                      code_step='data_exploration',
                                      code_writing_class=DataExplorationCodeProductsGPT,
                                      explain_code_class=RequestCodeExplanation,
                                      explain_created_files_class=None,
                                      ).get_code_and_output_and_descriptions()
            self.send_product_to_client('codes_and_outputs_with_explanations:data_exploration')

        # Goal
        self.advance_stage_and_set_active_conversation(ScientificStages.GOAL, ScientificAgent.Director)
        products.research_goal = director_converser.get_product_or_no_product_from_director(
            product_field='research_goal', returned_product=self.research_goal,
            acknowledge_no_product_message="OK. no problem. I will devise the goal myself.")
        is_auto_goal = products.research_goal is None
        if is_auto_goal:
            # we did not get a goal from the director, so we need to devise it ourselves:
            self.set_active_conversation(ScientificAgent.GoalReviewer)
            products.research_goal = GoalReviewGPT.from_(
                self,
                project_specific_goal_guidelines=self.project_specific_goal_guidelines
            ).run_and_get_valid_result()
        self.send_product_to_client('research_goal')

        goal_refinement_iteration = 0
        while True:
            # Literature search
            if self.should_do_literature_search:
                # TODO: need a dedicated client Stage for literature search
                self.advance_stage_and_set_active_conversation(ScientificStages.LITERATURE_REVIEW_GOAL,
                                                               ScientificAgent.CitationExpert)
                products.literature_search['goal'] = GoalLiteratureSearchReviewGPT.from_(
                    self, excluded_citation_titles=self.excluded_citation_titles,
                    stage=ScientificStages.LITERATURE_REVIEW_GOAL
                ).get_literature_search()
                self.send_product_to_client('literature_search_goal')

            if not is_auto_goal or goal_refinement_iteration == self.max_goal_refinement_iterations:
                break

            # Check if the goal is OK
            self.advance_stage_and_set_active_conversation(ScientificStages.ASSESS_NOVELTY, ScientificAgent.Writer)
            products.literature_search['goal'].scopes_to_queries_to_citations['goal and hypothesis'] = \
                {'cherry picked': GetMostSimilarCitations.from_(self).run_and_get_valid_result()}
            products.novelty_assessment = NoveltyAssessmentReview.from_(self).run_and_get_valid_result()
            if products.novelty_assessment['choice'] == 'OK':
                break

            # Goal is not OK, so we need to devise the goal according to the literature search:
            goal_refinement_iteration += 1
            self.advance_stage_and_set_active_conversation(ScientificStages.GOAL, ScientificAgent.Director)
            products.research_goal = ReGoalReviewGPT.from_(
                self,
                project_specific_goal_guidelines=self.project_specific_goal_guidelines
            ).run_and_get_valid_result()
            self.send_product_to_client('research_goal')
        self.send_product_to_client('research_goal', save_to_file=True, should_send=False)
        self.send_product_to_client('goal_and_novelty_assessment')

        # Plan
        self.advance_stage_and_set_active_conversation(ScientificStages.PLAN, ScientificAgent.PlanReviewer)

        # Hypotheses testing plan
        if self.should_prepare_hypothesis_testing_plan:
            products.hypothesis_testing_plan = \
                HypothesesTestingPlanReviewGPT.from_(self).run_and_get_valid_result()
            # self.send_product_to_client('hypothesis_testing_plan')

        self.send_product_to_client('hypothesis_testing_plan', save_to_file=True)

        # Data Preprocessing
        if self.should_do_data_preprocessing:
            # self.advance_stage_and_set_active_conversation(
            # ScientificStages.PREPROCESSING, ScientificAgent.DataPreprocessor)
            RequestCodeProducts.from_(self,
                                      code_step='data_preprocessing',
                                      code_writing_class=DataPreprocessingCodeProductsGPT,
                                      explain_code_class=RequestCodeExplanation,
                                      explain_created_files_class=None,
                                      ).get_code_and_output_and_descriptions()
            self.send_product_to_client('codes_and_outputs_with_explanations:data_preprocessing')

        # Analysis code and output
        self.advance_stage_and_set_active_conversation(ScientificStages.CODE, ScientificAgent.Debugger)
        RequestCodeProducts.from_(self,
                                  code_step='data_analysis',
                                  latex_document=self.latex_document,
                                  code_writing_class=DataAnalysisCodeProductsGPT,
                                  explain_code_class=RequestCodeExplanation,
                                  explain_created_files_class=None,
                                  ).get_code_and_output_and_descriptions()
        self.send_product_to_client('codes_and_outputs_with_explanations:data_analysis')
        self.advance_stage_and_set_active_conversation(ScientificStages.TABLES,
                                                       ScientificAgent.Debugger)
        RequestCodeProducts.from_(self,
                                  code_step='data_to_latex',
                                  latex_document=self.latex_document,
                                  code_writing_class=CreateLatexTablesCodeProductsGPT,
                                  explain_code_class=None,
                                  explain_created_files_class=None,
                                  ).get_code_and_output_and_descriptions()
        self.send_product_to_client('codes_and_outputs_with_explanations:data_to_latex')

        # literature review and scope
        self.advance_stage_and_set_active_conversation(ScientificStages.INTERPRETATION, ScientificAgent.Writer)
        products.paper_sections_and_optional_citations['title'], \
            products.paper_sections_and_optional_citations['abstract'] = \
            FirstTitleAbstractSectionWriterReviewGPT.from_(self, section_names=['title', 'abstract']
                                                           ).write_sections_with_citations()
        self.send_product_to_client('title_and_abstract_first')
        self.advance_stage_and_set_active_conversation(ScientificStages.LITERATURE_REVIEW_WRITING,
                                                       ScientificAgent.CitationExpert)
        products.literature_search['writing'] = WritingLiteratureSearchReviewGPT.from_(
            self, excluded_citation_titles=self.excluded_citation_titles).get_literature_search()
        self.send_product_to_client('scope_and_literature_search')

        # Paper sections
        for section_names, writing_class in sections_and_writing_class:
            # writing section
            if len(section_names) == 2:
                stage = ScientificStages.WRITING_TITLE_AND_ABSTRACT
            else:
                stage = SECTION_NAMES_TO_WRITING_STAGES[section_names[0]]
            self.advance_stage_and_set_active_conversation(stage, ScientificAgent.Writer)
            sections_with_citations = \
                writing_class.from_(self, section_names=section_names).write_sections_with_citations()
            for section_name, section_and_citations in zip(section_names, sections_with_citations):
                products.paper_sections_and_optional_citations[section_name] = section_and_citations
            if len(section_names) == 2:
                self.send_product_to_client('title_and_abstract')
            else:
                self.send_product_to_client(f'paper_sections:{section_names[0]}')

        # Compile paper
        paper_producer.assemble_compile_paper()

        return products
