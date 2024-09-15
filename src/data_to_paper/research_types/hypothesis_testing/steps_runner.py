from dataclasses import dataclass, field
from typing import Type

from data_to_paper.base_steps import DirectorProductGPT, DataStepRunner
from data_to_paper.latex.latex_doc import LatexDocument

from .app_startup import HypothesisTestingStartDialog
from .cast import ScientificAgent
from .coding.after_coding import RequestCodeExplanation, RequestCodeProducts
from .coding.analysis import DataAnalysisCodeProductsGPT
from .coding.exploration import DataExplorationCodeProductsGPT
from .coding.displayitems import CreateDisplayitemsCodeProductsGPT
from .coding.preprocessing import DataPreprocessingCodeProductsGPT
from .literature_search import WritingLiteratureSearchReviewGPT, GoalLiteratureSearchReviewGPT
from .produce_pdf_step import ProduceScientificPaperPDFWithAppendix
from .product_types import GoalAndHypothesisProduct
from .reviewing_steps import GoalReviewGPT, HypothesesTestingPlanReviewGPT, NoveltyAssessmentReview, ReGoalReviewGPT, \
    GetMostSimilarCitations
from .scientific_products import ScientificProducts
from .scientific_stage import ScientificStage
from .writing_steps import FirstTitleAbstractSectionWriterReviewGPT, SecondTitleAbstractSectionWriterReviewGPT, \
    MethodsSectionWriterReviewGPT, IntroductionSectionWriterReviewGPT, ResultsSectionWriterReviewGPT, \
    DiscussionSectionWriterReviewGPT

PAPER_SECTIONS_NAMES = ['title', 'abstract', 'introduction', 'results', 'discussion', 'methods']
SECTIONS_WITH_CITATIONS = ['introduction', 'discussion']

SKIP_STAGE_MESSAGE = 'This stage was skipped because the goal was provided by the user.'
SECTIONS_TO_WRITING_CLASS = [
    (('results',), ResultsSectionWriterReviewGPT),
    (('title', 'abstract'), SecondTitleAbstractSectionWriterReviewGPT),
    (('methods',), MethodsSectionWriterReviewGPT),
    (('introduction',), IntroductionSectionWriterReviewGPT),
    (('discussion',), DiscussionSectionWriterReviewGPT),
    # (('conclusion',), ConclusionSectionWriterReviewGPT),
]


@dataclass
class HypothesisTestingStepsRunner(DataStepRunner):
    PROJECT_PARAMETERS_FILENAME = 'data-to-paper-hypothesis-testing.json'
    DEFAULT_PROJECT_PARAMETERS = DataStepRunner.DEFAULT_PROJECT_PARAMETERS | dict(
        research_goal=None,
        should_do_data_exploration=True,
        should_do_data_preprocessing=False,
        should_prepare_hypothesis_testing_plan=True,
        should_do_literature_search=True,
        project_specific_goal_guidelines='',
        excluded_citation_titles=[],
        max_goal_refinement_iterations=3,
    )

    latex_document: LatexDocument = field(default_factory=LatexDocument)

    APP_STARTUP_CLS = HypothesisTestingStartDialog
    name = 'Hypothesis Testing Research'

    cast = ScientificAgent
    products: ScientificProducts = field(default_factory=ScientificProducts)
    stages: Type[ScientificStage] = ScientificStage

    goal_refinement_iteration: int = 0
    re_goal: bool = False

    def _pre_run_preparations(self):
        super()._pre_run_preparations()
        self.paper_producer = ProduceScientificPaperPDFWithAppendix.from_(
            self,
            output_filename='paper.pdf',
            paper_section_names=PAPER_SECTIONS_NAMES,
            figures_folder=self.output_directory,
        )

        self.stages_to_funcs = {
            ScientificStage.DATA: self._data_file_descriptions,
            ScientificStage.EXPLORATION: self._data_exploration,
            ScientificStage.GOAL: self._goal,
            ScientificStage.LITERATURE_REVIEW_GOAL: self._literature_search_goal,
            ScientificStage.ASSESS_NOVELTY: self._assess_novelty,
            ScientificStage.PLAN: self._hypotheses_testing_plan,
            ScientificStage.CODE: self._data_analysis,
            ScientificStage.DISPLAYITEMS: self._tables,
            ScientificStage.INTERPRETATION: self._interpretation,
            ScientificStage.LITERATURE_REVIEW_WRITING: self._literature_review_writing,
            ScientificStage.WRITING_RESULTS: self._writing_results,
            ScientificStage.WRITING_TITLE_AND_ABSTRACT: self._writing_title_and_abstract,
            ScientificStage.WRITING_METHODS: self._writing_methods,
            ScientificStage.WRITING_INTRODUCTION: self._writing_introduction,
            ScientificStage.WRITING_DISCUSSION: self._writing_discussion,
            ScientificStage.COMPILE: self._compile_paper,
        }

    """
    Stage functions
    """

    def _data_file_descriptions(self):
        self.director_converser = DirectorProductGPT.from_(
            self,
            assistant_agent=ScientificAgent.Director,
            user_agent=ScientificAgent.Performer,
            conversation_name='with_director',
        )
        self.products.data_file_descriptions = self.director_converser.get_product_or_no_product_from_director(
            product_name='Data description', returned_product=self.data_file_descriptions)
        self.send_product_to_client('data_file_descriptions')

    def _data_exploration(self):
        if not self.project_parameters['should_do_data_exploration']:
            return
        RequestCodeProducts.from_(
            self,
            code_step='data_exploration',
            code_writing_class=DataExplorationCodeProductsGPT,
            explain_code_class=RequestCodeExplanation,
            explain_created_files_class=None,
        ).get_code_and_output_and_descriptions()
        self.send_product_to_client('codes_and_outputs_with_explanations:data_exploration')

    def _literature_search_goal(self):
        if not self.project_parameters['should_do_literature_search']:
            return
        GoalLiteratureSearchReviewGPT.from_(
            self, excluded_citation_titles=self.project_parameters['excluded_citation_titles'],
            literature_search=self.products.literature_search['goal']
        ).get_literature_search()
        self.send_product_to_client('literature_search:goal')

    def _assess_novelty(self):
        self.products.most_similar_papers = GetMostSimilarCitations.from_(self).run_and_get_valid_result()
        self.products.novelty_assessment = NoveltyAssessmentReview.from_(self).run_and_get_valid_result()
        self.send_product_to_client('novelty_assessment')
        self.goal_refinement_iteration += 1
        if (not self.products.novelty_assessment['choice'] == 'OK' and
                self.goal_refinement_iteration < self.project_parameters['max_goal_refinement_iterations']):
            self.re_goal = True
            return ScientificStage.GOAL

    def _goal(self):
        next_stage = None
        if not self.re_goal:
            research_goal = self.director_converser.get_product_or_no_product_from_director(
                product_name='Research Goal', returned_product=self.project_parameters['research_goal'],
                acknowledge_no_product_message="OK. no problem. I will devise the goal myself.")
            if research_goal is None:
                # Goal not provided by the user
                self.products.research_goal = GoalReviewGPT.from_(
                    self,
                    project_specific_goal_guidelines=self.project_parameters['project_specific_goal_guidelines']
                ).run_and_get_valid_result()
            else:
                self.products.research_goal = GoalAndHypothesisProduct(value=research_goal)
                self._app_send_product_of_stage(ScientificStage.LITERATURE_REVIEW_GOAL, SKIP_STAGE_MESSAGE)
                self._app_send_product_of_stage(ScientificStage.ASSESS_NOVELTY, SKIP_STAGE_MESSAGE)
                next_stage = ScientificStage.PLAN
        else:
            self.products.research_goal = ReGoalReviewGPT.from_(
                self,
                project_specific_goal_guidelines=self.project_parameters['project_specific_goal_guidelines']
            ).run_and_get_valid_result()
        self.send_product_to_client('research_goal', save_to_file=True)
        return next_stage

    def _hypotheses_testing_plan(self):
        if not self.project_parameters['should_prepare_hypothesis_testing_plan']:
            return
        self.products.hypothesis_testing_plan = HypothesesTestingPlanReviewGPT.from_(
            self).run_and_get_valid_result()
        self.send_product_to_client('hypothesis_testing_plan', save_to_file=True)

    def _data_preprocessing(self):
        if not self.project_parameters['should_do_data_preprocessing']:
            return
        RequestCodeProducts.from_(
            self,
            code_step='data_preprocessing',
            code_writing_class=DataPreprocessingCodeProductsGPT,
            explain_code_class=RequestCodeExplanation,
            explain_created_files_class=None,
        ).get_code_and_output_and_descriptions()
        self.send_product_to_client('codes_and_outputs_with_explanations:data_preprocessing')

    def _data_analysis(self):
        RequestCodeProducts.from_(
            self,
            code_step='data_analysis',
            code_writing_class=DataAnalysisCodeProductsGPT,
            explain_code_class=RequestCodeExplanation,
            explain_created_files_class=None,
        ).get_code_and_output_and_descriptions()
        self.send_product_to_client('codes_and_outputs_with_explanations:data_analysis')

    def _tables(self):
        RequestCodeProducts.from_(
            self,
            code_step='data_to_latex',
            latex_document=self.latex_document,
            code_writing_class=CreateDisplayitemsCodeProductsGPT,
            explain_code_class=None,
            explain_created_files_class=None,
        ).get_code_and_output_and_descriptions()
        self.send_product_to_client('codes_and_outputs_with_explanations:data_to_latex')

    def _interpretation(self):
        self.products.paper_sections_and_optional_citations['title'], \
            self.products.paper_sections_and_optional_citations['abstract'] = \
            FirstTitleAbstractSectionWriterReviewGPT.from_(
                self, section_names=['title', 'abstract']).write_sections_with_citations()
        self.send_product_to_client('title_and_abstract_first')

    def _literature_review_writing(self):
        WritingLiteratureSearchReviewGPT.from_(
            self,
            literature_search=self.products.literature_search['writing'],
            excluded_citation_titles=self.project_parameters['excluded_citation_titles']
        ).get_literature_search()
        self.send_product_to_client('literature_search:writing')

    def _writing_paper_section(self, section_names, writing_class):
        sections_with_citations = \
            writing_class.from_(self, section_names=section_names).write_sections_with_citations()
        for section_name, section_and_citations in zip(section_names, sections_with_citations):
            self.products.paper_sections_and_optional_citations[section_name] = section_and_citations
        if len(section_names) == 2:
            self.send_product_to_client('title_and_abstract')
        else:
            self.send_product_to_client(f'paper_sections:{section_names[0]}')

    def _writing_results(self):
        self._writing_paper_section(('results',), ResultsSectionWriterReviewGPT)

    def _writing_title_and_abstract(self):
        self._writing_paper_section(('title', 'abstract'), SecondTitleAbstractSectionWriterReviewGPT)

    def _writing_methods(self):
        self._writing_paper_section(('methods',), MethodsSectionWriterReviewGPT)

    def _writing_introduction(self):
        self._writing_paper_section(('introduction',), IntroductionSectionWriterReviewGPT)

    def _writing_discussion(self):
        self._writing_paper_section(('discussion',), DiscussionSectionWriterReviewGPT)

    def _compile_paper(self):
        self.paper_producer.assemble_compile_paper()
        self._app_clear_panels()
        self._app_send_product_of_stage(
            ScientificStage.COMPILE,
            f'<a href="file://{self.output_directory}/paper.pdf">Download the manuscript</a>')
