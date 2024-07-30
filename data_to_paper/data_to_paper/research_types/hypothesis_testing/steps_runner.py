import os
import pathlib
from dataclasses import dataclass, field
from typing import Tuple, Type, List, Union

from data_to_paper.base_steps import DirectorProductGPT, CheckLatexCompilation, DataStepRunner
from .app_startup import HypothesisTestingStartDialog

from .cast import ScientificAgent
from .coding.after_coding import RequestCodeExplanation, RequestCodeProducts
from .coding.latex_tables import CreateLatexTablesCodeProductsGPT
from .coding.preprocessing import DataPreprocessingCodeProductsGPT
from .coding.data_analysis import DataAnalysisCodeProductsGPT
from .coding.data_exploration import DataExplorationCodeProductsGPT
from .literature_search import WritingLiteratureSearchReviewGPT, GoalLiteratureSearchReviewGPT
from .produce_pdf_step import ProduceScientificPaperPDFWithAppendix
from .product_types import GoalAndHypothesisProduct
from .scientific_products import ScientificProducts
from .scientific_stage import ScientificStage, SECTION_NAMES_TO_WRITING_STAGES
from .reviewing_steps import GoalReviewGPT, HypothesesTestingPlanReviewGPT, NoveltyAssessmentReview, ReGoalReviewGPT, \
    GetMostSimilarCitations
from .writing_steps import SectionWriterReviewBackgroundProductsConverser, \
    FirstTitleAbstractSectionWriterReviewGPT, SecondTitleAbstractSectionWriterReviewGPT, \
    MethodsSectionWriterReviewGPT, IntroductionSectionWriterReviewGPT, ResultsSectionWriterReviewGPT, \
    DiscussionSectionWriterReviewGPT
from ...conversation.stage import Stage

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
class HypothesisTestingStepsRunner(DataStepRunner, CheckLatexCompilation):
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

    APP_STARTUP_CLS = HypothesisTestingStartDialog
    name = 'Hypothesis Testing Research'

    cast = ScientificAgent
    products: ScientificProducts = field(default_factory=ScientificProducts)
    stages: Type[ScientificStage] = ScientificStage

    def _create_temp_folder_to_run_in(self):
        return self.temp_folder_to_run_in

    def get_sections_to_writing_class(
            self) -> List[Tuple[Union[str, Tuple[str, ...]], Type[SectionWriterReviewBackgroundProductsConverser]]]:
        return SECTIONS_TO_WRITING_CLASS

    def assert_paper_sections_to_write_matches_template(self, template_sections, sections_to_writing_class):
        flattened_paper_sections_to_write = []
        for sections, _ in sections_to_writing_class:
            flattened_paper_sections_to_write.extend(sections)
        assert set(flattened_paper_sections_to_write) == set(template_sections)

    def _add_stage_name_to_api_usage_cost_file(self, stage_name):
        with open(self._get_path_in_output_directory(self.API_USAGE_COST_FILENAME), 'r') as f:
            lines = f.readlines()
            existing_stage_names = set([line.strip()[:-1] for line in lines if line.strip().endswith(':')])
        if stage_name in existing_stage_names:
            return
        with open(self._get_path_in_output_directory(self.API_USAGE_COST_FILENAME), 'a') as f:
            f.write(f'{stage_name}:\n')

    @staticmethod
    def _pretty_api_usage_cost(api_usage_cost_file: str) -> str:
        with open(api_usage_cost_file, 'r') as f:
            lines = f.readlines()

        result = '<h2>The API usage cost for each step:</h2>\n'
        current_step = None
        current_cost = 0.0
        step_found = False

        for line in lines:
            line = line.strip()
            if line.endswith(':'):
                if current_step:
                    result += f'<li style="color:white;">\n<b>{current_step}:</b> {current_cost:.2f}\n</li>\n'
                current_step = line[:-1]
                current_cost = 0.0
                step_found = True
            elif line:
                current_cost += float(line)
                step_found = True

        if current_step:
            result += f'<li style="color:white;">\n<b>{current_step}:</b> {current_cost:.2f}\n</li>\n'

        return result

    def _pre_run_preparations(self):
        """
        create the api usage cost file
        """
        if not pathlib.Path(self._get_path_in_output_directory(self.API_USAGE_COST_FILENAME)).exists():
            with open(self._get_path_in_output_directory(self.API_USAGE_COST_FILENAME), 'w') as f:
                f.write('')
        super()._pre_run_preparations()

    def advance_stage(self, stage: Union[Stage, bool]):
        self._app_send_api_usage_cost(self._pretty_api_usage_cost(
            self._get_path_in_output_directory(self.API_USAGE_COST_FILENAME)))
        if isinstance(stage, Stage):
            self._add_stage_name_to_api_usage_cost_file(stage.name)
        super().advance_stage(stage)

    def _run_all_steps(self) -> ScientificProducts:
        products = self.products  # Start with empty products

        # Set the paper section names:
        sections_and_writing_class = self.get_sections_to_writing_class()
        self.assert_paper_sections_to_write_matches_template(PAPER_SECTIONS_NAMES, sections_and_writing_class)
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
        self.advance_stage(ScientificStage.DATA)
        products.data_file_descriptions = director_converser.get_product_or_no_product_from_director(
            product_name='Data description', returned_product=self.data_file_descriptions)
        self.send_product_to_client('data_file_descriptions')

        # Data exploration
        if self.project_parameters['should_do_data_exploration']:
            self.advance_stage(ScientificStage.EXPLORATION)
            RequestCodeProducts.from_(self,
                                      code_step='data_exploration',
                                      code_writing_class=DataExplorationCodeProductsGPT,
                                      explain_code_class=RequestCodeExplanation,
                                      explain_created_files_class=None,
                                      ).get_code_and_output_and_descriptions()
            self.send_product_to_client('codes_and_outputs_with_explanations:data_exploration')

        # Goal
        self.advance_stage(ScientificStage.GOAL)
        research_goal = director_converser.get_product_or_no_product_from_director(
                product_name='Research Goal', returned_product=self.project_parameters['research_goal'],
                acknowledge_no_product_message="OK. no problem. I will devise the goal myself.")
        if research_goal is None:
            # we did not get a goal from the director, so we need to devise it ourselves:
            products.research_goal = GoalReviewGPT.from_(
                self,
                project_specific_goal_guidelines=self.project_parameters['project_specific_goal_guidelines']
            ).run_and_get_valid_result()
            self.send_product_to_client('research_goal')

            goal_refinement_iteration = 0
            while True:
                # Literature search
                if self.project_parameters['should_do_literature_search']:
                    self.advance_stage(ScientificStage.LITERATURE_REVIEW_GOAL)
                    GoalLiteratureSearchReviewGPT.from_(
                        self, excluded_citation_titles=self.project_parameters['excluded_citation_titles'],
                        literature_search=products.literature_search['goal']
                    ).get_literature_search()
                    self.send_product_to_client('literature_search:goal')

                if goal_refinement_iteration == self.project_parameters['max_goal_refinement_iterations']:
                    break

                # Check if the goal is OK
                self.advance_stage(ScientificStage.ASSESS_NOVELTY)
                products.most_similar_papers = GetMostSimilarCitations.from_(self).run_and_get_valid_result()
                products.novelty_assessment = NoveltyAssessmentReview.from_(self).run_and_get_valid_result()
                self.send_product_to_client('novelty_assessment')
                if products.novelty_assessment['choice'] == 'OK':
                    break

                # Goal is not OK, so we need to devise the goal according to the literature search:
                goal_refinement_iteration += 1
                self.advance_stage(ScientificStage.GOAL)
                products.research_goal = ReGoalReviewGPT.from_(
                    self,
                    project_specific_goal_guidelines=self.project_parameters['project_specific_goal_guidelines']
                ).run_and_get_valid_result()
                self.send_product_to_client('research_goal', save_to_file=True)
        else:
            products.research_goal = GoalAndHypothesisProduct(value=research_goal)
            self._app_send_product_of_stage(ScientificStage.LITERATURE_REVIEW_GOAL,
                                            'This stage was skipped because the goal was provided by the user.')
            self._app_send_product_of_stage(ScientificStage.ASSESS_NOVELTY,
                                            'This stage was skipped because the goal was provided by the user.')
            self.send_product_to_client('research_goal', save_to_file=True)

        # Plan
        self.advance_stage(ScientificStage.PLAN)

        # Hypotheses testing plan
        if self.project_parameters['should_prepare_hypothesis_testing_plan']:
            products.hypothesis_testing_plan = \
                HypothesesTestingPlanReviewGPT.from_(self).run_and_get_valid_result()
            # self.send_product_to_client('hypothesis_testing_plan')

        self.send_product_to_client('hypothesis_testing_plan', save_to_file=True)

        # Data Preprocessing
        if self.project_parameters['should_do_data_preprocessing']:
            # self.advance_stage(ScientificStage.PREPROCESSING)
            RequestCodeProducts.from_(self,
                                      code_step='data_preprocessing',
                                      code_writing_class=DataPreprocessingCodeProductsGPT,
                                      explain_code_class=RequestCodeExplanation,
                                      explain_created_files_class=None,
                                      ).get_code_and_output_and_descriptions()
            self.send_product_to_client('codes_and_outputs_with_explanations:data_preprocessing')

        # Analysis code and output
        self.advance_stage(ScientificStage.CODE)
        RequestCodeProducts.from_(self,
                                  code_step='data_analysis',
                                  latex_document=self.latex_document,
                                  code_writing_class=DataAnalysisCodeProductsGPT,
                                  explain_code_class=RequestCodeExplanation,
                                  explain_created_files_class=None,
                                  ).get_code_and_output_and_descriptions()
        self.send_product_to_client('codes_and_outputs_with_explanations:data_analysis')
        self.advance_stage(ScientificStage.TABLES)
        RequestCodeProducts.from_(self,
                                  code_step='data_to_latex',
                                  latex_document=self.latex_document,
                                  code_writing_class=CreateLatexTablesCodeProductsGPT,
                                  explain_code_class=None,
                                  explain_created_files_class=None,
                                  ).get_code_and_output_and_descriptions()
        self.send_product_to_client('codes_and_outputs_with_explanations:data_to_latex')

        # literature review and scope
        self.advance_stage(ScientificStage.INTERPRETATION)
        products.paper_sections_and_optional_citations['title'], \
            products.paper_sections_and_optional_citations['abstract'] = \
            FirstTitleAbstractSectionWriterReviewGPT.from_(self, section_names=['title', 'abstract']
                                                           ).write_sections_with_citations()
        self.send_product_to_client('title_and_abstract_first')
        self.advance_stage(ScientificStage.LITERATURE_REVIEW_WRITING)
        WritingLiteratureSearchReviewGPT.from_(
            self,
            literature_search=products.literature_search['writing'],
            excluded_citation_titles=self.project_parameters['excluded_citation_titles']).get_literature_search()
        self.send_product_to_client('literature_search:writing')

        # Paper sections
        for section_names, writing_class in sections_and_writing_class:
            # writing section
            if len(section_names) == 2:
                stage = ScientificStage.WRITING_TITLE_AND_ABSTRACT
            else:
                stage = SECTION_NAMES_TO_WRITING_STAGES[section_names[0]]
            self.advance_stage(stage)
            sections_with_citations = \
                writing_class.from_(self, section_names=section_names).write_sections_with_citations()
            for section_name, section_and_citations in zip(section_names, sections_with_citations):
                products.paper_sections_and_optional_citations[section_name] = section_and_citations
            if len(section_names) == 2:
                self.send_product_to_client('title_and_abstract')
            else:
                self.send_product_to_client(f'paper_sections:{section_names[0]}')

        # Compile paper
        self.advance_stage(ScientificStage.COMPILE)
        paper_producer.assemble_compile_paper()
        self._app_clear_panels()
        self._app_send_product_of_stage(
            ScientificStage.COMPILE,
            f'<a href="file://{self.output_directory}/paper.pdf">Download the manuscript</a>')
        self.advance_stage(True)

        return products
