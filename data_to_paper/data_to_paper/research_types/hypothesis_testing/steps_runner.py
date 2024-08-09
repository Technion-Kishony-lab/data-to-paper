from dataclasses import dataclass, field
from typing import Type, Union, Dict

from data_to_paper.base_steps import DirectorProductGPT, CheckLatexCompilation, DataStepRunner
from data_to_paper.conversation.stage import Stage
from data_to_paper.servers.json_dump import load_from_json, dump_to_json

from .app_startup import HypothesisTestingStartDialog
from .cast import ScientificAgent
from .coding.after_coding import RequestCodeExplanation, RequestCodeProducts
from .coding.data_analysis import DataAnalysisCodeProductsGPT
from .coding.data_exploration import DataExplorationCodeProductsGPT
from .coding.latex_tables import CreateLatexTablesCodeProductsGPT
from .coding.preprocessing import DataPreprocessingCodeProductsGPT
from .literature_search import WritingLiteratureSearchReviewGPT, GoalLiteratureSearchReviewGPT
from .produce_pdf_step import ProduceScientificPaperPDFWithAppendix
from .product_types import GoalAndHypothesisProduct
from .reviewing_steps import GoalReviewGPT, HypothesesTestingPlanReviewGPT, NoveltyAssessmentReview, ReGoalReviewGPT, \
    GetMostSimilarCitations
from .scientific_products import ScientificProducts
from .scientific_stage import ScientificStage, SECTION_NAMES_TO_WRITING_STAGES
from .writing_steps import FirstTitleAbstractSectionWriterReviewGPT, SecondTitleAbstractSectionWriterReviewGPT, \
    MethodsSectionWriterReviewGPT, IntroductionSectionWriterReviewGPT, ResultsSectionWriterReviewGPT, \
    DiscussionSectionWriterReviewGPT

PAPER_SECTIONS_NAMES = ['title', 'abstract', 'introduction', 'results', 'discussion', 'methods']
SECTIONS_WITH_CITATIONS = ['introduction', 'discussion']


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

    num_conversations_at_each_stage: Dict = field(default_factory=dict)

    goal_refinement_iteration: int = 0
    re_goal: bool = False

    def __post_init__(self):
        self.paper_producer = ProduceScientificPaperPDFWithAppendix.from_(
            self,
            latex_document=self.latex_document,
            output_filename='paper.pdf',
            paper_section_names=PAPER_SECTIONS_NAMES,
        )

        self.stage_to_func = {
            ScientificStage.DATA: self._data_file_descriptions,
            ScientificStage.EXPLORATION: self._data_exploration,
            ScientificStage.GOAL: self._goal,
            ScientificStage.LITERATURE_REVIEW_GOAL: self._literature_search_goal,
            ScientificStage.ASSESS_NOVELTY: self._assess_novelty,
            ScientificStage.PLAN: self._hypotheses_testing_plan,
            ScientificStage.CODE: self._data_analysis,
            ScientificStage.TABLES: self._tables,
            ScientificStage.INTERPRETATION: self._interpretation,
            ScientificStage.LITERATURE_REVIEW_WRITING: self._literature_review_writing,
            ScientificStage.WRITING_RESULTS: self._writing_results,
            ScientificStage.WRITING_TITLE_AND_ABSTRACT: self._writing_title_and_abstract,
            ScientificStage.WRITING_METHODS: self._writing_methods,
            ScientificStage.WRITING_INTRODUCTION: self._writing_introduction,
            ScientificStage.WRITING_DISCUSSION: self._writing_discussion,
            ScientificStage.COMPILE: self._compile_paper,
        }

    def _create_temp_folder_to_run_in(self):
        return self.temp_folder_to_run_in

    @staticmethod
    def _pretty_api_usage_cost(api_usage_cost_file: str) -> str:
        data = load_from_json(api_usage_cost_file)

        result = '<h2>The API usage cost for each step:</h2>\n'

        for step, cost in data.items():
            result += f'<li style="color:white;">\n<b>{step}:</b> {cost:.2f}$\n</li>\n'

        return result

    def _pre_run_preparations(self):
        """
        create the api usage cost file
        """
        dump_to_json({}, self._get_path_in_output_directory(self.API_USAGE_COST_FILENAME))
        super()._pre_run_preparations()

    def _add_stage_name_to_api_usage_cost_file(self, stage_name):
        data = load_from_json(self._get_path_in_output_directory(self.API_USAGE_COST_FILENAME))
        data[stage_name] = 0
        dump_to_json(data, self._get_path_in_output_directory(self.API_USAGE_COST_FILENAME))

    def advance_stage(self, stage: Union[Stage, bool]):
        if isinstance(stage, Stage):
            self._add_stage_name_to_api_usage_cost_file(stage.name)
            if stage.name not in self.num_conversations_at_each_stage:
                self.num_conversations_at_each_stage[stage.name] = len(self.actions_and_conversations.conversations)
        super().advance_stage(stage)

    def app_send_api_usage_cost(self):
        self._app_send_api_usage_cost(self._pretty_api_usage_cost(
            self._get_path_in_output_directory(self.API_USAGE_COST_FILENAME)))

    def reset_to_stage(self, stage: ScientificStage):
        # Reset the server caller to the step
        self.server_caller.reset_to_stage(stage)

        # delete all conversations in the actions_and_conversations of the steps after and including the step
        conversation_names = list(self.actions_and_conversations.conversations.keys())
        conversations_to_delete = conversation_names[self.num_conversations_at_each_stage[stage.name]:]
        for conversation in conversations_to_delete:
            del self.actions_and_conversations.conversations[conversation]

        self.app_send_api_usage_cost()

    def _data_file_descriptions(self):
        self.director_converser = DirectorProductGPT.from_(
            self,
            assistant_agent=ScientificAgent.Director,
            user_agent=ScientificAgent.Performer,
            conversation_name='with_director',
        )
        self.advance_stage(ScientificStage.DATA)
        self.products.data_file_descriptions = self.director_converser.get_product_or_no_product_from_director(
            product_name='Data description', returned_product=self.data_file_descriptions)
        self.send_product_to_client('data_file_descriptions')

    def _data_exploration(self):
        if self.project_parameters['should_do_data_exploration']:
            self.advance_stage(ScientificStage.EXPLORATION)
            RequestCodeProducts.from_(
                self,
                code_step='data_exploration',
                code_writing_class=DataExplorationCodeProductsGPT,
                explain_code_class=RequestCodeExplanation,
                explain_created_files_class=None,
            ).get_code_and_output_and_descriptions()
            self.send_product_to_client('codes_and_outputs_with_explanations:data_exploration')

    def _literature_search_goal(self):
        if self.project_parameters['should_do_literature_search']:
            self.advance_stage(ScientificStage.LITERATURE_REVIEW_GOAL)
            GoalLiteratureSearchReviewGPT.from_(
                self, excluded_citation_titles=self.project_parameters['excluded_citation_titles'],
                literature_search=self.products.literature_search['goal']
            ).get_literature_search()
            self.send_product_to_client('literature_search:goal')

    def _assess_novelty(self):
        self.advance_stage(ScientificStage.ASSESS_NOVELTY)
        self.products.most_similar_papers = GetMostSimilarCitations.from_(self).run_and_get_valid_result()
        self.products.novelty_assessment = NoveltyAssessmentReview.from_(self).run_and_get_valid_result()
        self.send_product_to_client('novelty_assessment')
        self.goal_refinement_iteration += 1
        if (not self.products.novelty_assessment['choice'] == 'OK' and
                self.goal_refinement_iteration < self.project_parameters['max_goal_refinement_iterations']):
            self.re_goal = True
            self._reset_is_stage_completed(ScientificStage.GOAL)

    def _goal(self):
        if not self.re_goal:
            self.advance_stage(ScientificStage.GOAL)
            research_goal = self.director_converser.get_product_or_no_product_from_director(
                product_name='Research Goal', returned_product=self.project_parameters['research_goal'],
                acknowledge_no_product_message="OK. no problem. I will devise the goal myself.")
            if research_goal is None:
                self.products.research_goal = GoalReviewGPT.from_(
                    self,
                    project_specific_goal_guidelines=self.project_parameters['project_specific_goal_guidelines']
                ).run_and_get_valid_result()
                self.send_product_to_client('research_goal')
            else:
                self.products.research_goal = GoalAndHypothesisProduct(value=research_goal)
                self._app_send_product_of_stage(ScientificStage.LITERATURE_REVIEW_GOAL,
                                                'This stage was skipped because the goal was provided by the user.')
                self._app_send_product_of_stage(ScientificStage.ASSESS_NOVELTY,
                                                'This stage was skipped because the goal was provided by the user.')
                self.send_product_to_client('research_goal', save_to_file=True)
        else:
            self.advance_stage(ScientificStage.GOAL)
            self.products.research_goal = ReGoalReviewGPT.from_(
                self,
                project_specific_goal_guidelines=self.project_parameters['project_specific_goal_guidelines']
            ).run_and_get_valid_result()
            self.send_product_to_client('research_goal', save_to_file=True)

    def _hypotheses_testing_plan(self):
        self.advance_stage(ScientificStage.PLAN)
        if self.project_parameters['should_prepare_hypothesis_testing_plan']:
            self.products.hypothesis_testing_plan = HypothesesTestingPlanReviewGPT.from_(
                self).run_and_get_valid_result()
            self.send_product_to_client('hypothesis_testing_plan', save_to_file=True)

    def _data_preprocessing(self):
        if self.project_parameters['should_do_data_preprocessing']:
            RequestCodeProducts.from_(
                self,
                code_step='data_preprocessing',
                code_writing_class=DataPreprocessingCodeProductsGPT,
                explain_code_class=RequestCodeExplanation,
                explain_created_files_class=None,
            ).get_code_and_output_and_descriptions()
            self.send_product_to_client('codes_and_outputs_with_explanations:data_preprocessing')

    def _data_analysis(self):
        self.advance_stage(ScientificStage.CODE)
        RequestCodeProducts.from_(
            self,
            code_step='data_analysis',
            latex_document=self.latex_document,
            code_writing_class=DataAnalysisCodeProductsGPT,
            explain_code_class=RequestCodeExplanation,
            explain_created_files_class=None,
        ).get_code_and_output_and_descriptions()
        self.send_product_to_client('codes_and_outputs_with_explanations:data_analysis')

    def _tables(self):
        self.advance_stage(ScientificStage.TABLES)
        RequestCodeProducts.from_(
            self,
            code_step='data_to_latex',
            latex_document=self.latex_document,
            code_writing_class=CreateLatexTablesCodeProductsGPT,
            explain_code_class=None,
            explain_created_files_class=None,
        ).get_code_and_output_and_descriptions()
        self.send_product_to_client('codes_and_outputs_with_explanations:data_to_latex')

    def _interpretation(self):
        self.advance_stage(ScientificStage.INTERPRETATION)
        self.products.paper_sections_and_optional_citations['title'], \
            self.products.paper_sections_and_optional_citations['abstract'] = \
            FirstTitleAbstractSectionWriterReviewGPT.from_(
                self, section_names=['title', 'abstract']).write_sections_with_citations()
        self.send_product_to_client('title_and_abstract_first')

    def _literature_review_writing(self):
        self.advance_stage(ScientificStage.LITERATURE_REVIEW_WRITING)
        WritingLiteratureSearchReviewGPT.from_(
            self,
            literature_search=self.products.literature_search['writing'],
            excluded_citation_titles=self.project_parameters['excluded_citation_titles']
        ).get_literature_search()
        self.send_product_to_client('literature_search:writing')

    def _writing_paper_section(self, sections_and_writing_class):
        section_names, writing_class = sections_and_writing_class
        if len(section_names) == 2:
            stage = ScientificStage.WRITING_TITLE_AND_ABSTRACT
        else:
            stage = SECTION_NAMES_TO_WRITING_STAGES[section_names[0]]
        self.advance_stage(stage)
        sections_with_citations = \
            writing_class.from_(self, section_names=section_names).write_sections_with_citations()
        for section_name, section_and_citations in zip(section_names, sections_with_citations):
            self.products.paper_sections_and_optional_citations[section_name] = section_and_citations
        if len(section_names) == 2:
            self.send_product_to_client('title_and_abstract')
        else:
            self.send_product_to_client(f'paper_sections:{section_names[0]}')

    def _writing_results(self):
        self._writing_paper_section((('results',), ResultsSectionWriterReviewGPT))

    def _writing_title_and_abstract(self):
        self._writing_paper_section((('title', 'abstract'), SecondTitleAbstractSectionWriterReviewGPT))

    def _writing_methods(self):
        self._writing_paper_section((('methods',), MethodsSectionWriterReviewGPT))

    def _writing_introduction(self):
        self._writing_paper_section((('introduction',), IntroductionSectionWriterReviewGPT))

    def _writing_discussion(self):
        self._writing_paper_section((('discussion',), DiscussionSectionWriterReviewGPT))

    def _compile_paper(self):
        self.advance_stage(ScientificStage.COMPILE)
        self.paper_producer.assemble_compile_paper()
        self._app_clear_panels()
        self._app_send_product_of_stage(
            ScientificStage.COMPILE,
            f'<a href="file://{self.output_directory}/paper.pdf">Download the manuscript</a>')
        self.advance_stage(True)
