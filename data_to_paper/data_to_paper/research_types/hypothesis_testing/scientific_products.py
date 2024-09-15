from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Tuple, Set, List, Union

from data_to_paper.base_products.file_descriptions import DataFileDescriptions, DataFileDescription
from data_to_paper.base_steps import LiteratureSearch
from data_to_paper.base_steps.literature_search import LiteratureSearchParams
from data_to_paper.code_and_output_files.file_view_params import ViewPurpose
from data_to_paper.code_and_output_files.ref_numeric_values import replace_hyperlinks_with_values
from data_to_paper.code_and_output_files.referencable_text import hypertarget_if_referencable_text_product
from data_to_paper.conversation.stage import Stage
from data_to_paper.latex import extract_latex_section_from_response
from data_to_paper.latex.latex_to_pdf import evaluate_latex_num_command
from data_to_paper.latex.tables import add_displayitems_to_paper_section, get_displayitem_caption

from data_to_paper.research_types.hypothesis_testing.cast import ScientificAgent
from data_to_paper.research_types.hypothesis_testing.product_types import HypothesisTestingPlanProduct, \
    NoveltyAssessmentProduct, GoalAndHypothesisProduct, MostSimilarPapersProduct, NoveltySummaryProduct
from data_to_paper.research_types.hypothesis_testing.scientific_stage import ScientificStage, \
    SECTION_NAMES_TO_WRITING_STAGES
from data_to_paper.code_and_output_files.code_and_output import CodeAndOutput

from data_to_paper.utils.nice_list import NiceList
from data_to_paper.base_products import Products, NameDescriptionStageGenerator, ProductGenerator
from data_to_paper.utils.types import ListBasedSet, MemoryDict
from data_to_paper.servers.custom_types import Citation

CODE_STEPS_TO_STAGES_NAMES_AGENTS: Dict[str, Tuple[Stage, str, ScientificAgent]] = {
    'data_exploration': (ScientificStage.EXPLORATION, 'Data Exploration', ScientificAgent.DataExplorer),
    # 'data_preprocessing': (ScientificStage.PREPROCESSING, 'Data Preprocessing', ScientificAgent.DataPreprocessor),
    'data_analysis': (ScientificStage.CODE, 'Data Analysis', ScientificAgent.Debugger),
    'data_to_latex': (ScientificStage.DISPLAYITEMS, 'LaTeX Table Design', ScientificAgent.InterpretationReviewer),
}


class HypertargetPrefix(Enum):
    """
    Prefixes for hypertargets.
    """
    GENERAL_FILE_DESCRIPTION = 'S'
    FILE_DESCRIPTIONS = ('T', 'U', 'V', 'W', 'X', 'Y', 'Z')
    ADDITIONAL_RESULTS = ('R',)
    LATEX_TABLES = ('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H')


def get_code_stage(code_step: str) -> Stage:
    """
    Return the stage of the code step.
    """
    return CODE_STEPS_TO_STAGES_NAMES_AGENTS[code_step][0]


def get_code_name(code_step: str) -> str:
    """
    Return the name of the code step.
    """
    return CODE_STEPS_TO_STAGES_NAMES_AGENTS[code_step][1]


def get_code_agent(code_step: str) -> ScientificAgent:
    """
    Return the agent of the code step.
    """
    return CODE_STEPS_TO_STAGES_NAMES_AGENTS[code_step][2]


def convert_description_of_created_files_to_string(description_of_created_files: Dict[str, str]) -> Optional[str]:
    """
    Convert the description of created files to a string.
    """
    if not description_of_created_files:
        return None
    return '\n'.join(
        f'File "{file_name}":\n\n{file_description}'
        for file_name, file_description in description_of_created_files.items()
    )


STAGE_AND_SCOPE_TO_LITERATURE_SEARCH_PARAMS = {
    'goal': ({
        'dataset': LiteratureSearchParams(12, 2, 2.0, False),
        'questions': LiteratureSearchParams(12, 2, 2.0, False),
    }, "Literature Search for Goal", ScientificStage.LITERATURE_REVIEW_GOAL),
    'writing': ({
        'background': LiteratureSearchParams(12, 5, 2.0, True),
        'dataset': LiteratureSearchParams(12, 2, 2.0, False),
        'methods': LiteratureSearchParams(6, 10, 1.5, False),
        'results': LiteratureSearchParams(12, 1, 2.0, True),
    }, "Literature Search for Writing", ScientificStage.LITERATURE_REVIEW_WRITING),
}


def _create_literature_search(stage: str) -> LiteratureSearch:
    params = STAGE_AND_SCOPE_TO_LITERATURE_SEARCH_PARAMS[stage]
    return LiteratureSearch(name=params[1], stage=params[2], scopes_to_search_params=params[0])


def _get_literature_searchs() -> Dict[str, LiteratureSearch]:
    return {stage: _create_literature_search(stage) for stage in STAGE_AND_SCOPE_TO_LITERATURE_SEARCH_PARAMS}


@dataclass
class ScientificProducts(Products):
    """
    All products of the scientific process.
    """
    data_file_descriptions: DataFileDescriptions = field(default_factory=DataFileDescriptions)
    codes_and_outputs: Dict[str, CodeAndOutput] = field(default_factory=dict)
    research_goal: GoalAndHypothesisProduct = None
    novelty_assessment: NoveltyAssessmentProduct = None
    literature_search: Dict[str, LiteratureSearch] = field(default_factory=_get_literature_searchs)
    most_similar_papers: MostSimilarPapersProduct = None
    hypothesis_testing_plan: HypothesisTestingPlanProduct = None
    paper_sections_and_optional_citations: Dict[str, Union[str, Tuple[str, Set[Citation]]]] = \
        field(default_factory=MemoryDict)

    def get_created_dfs(self) -> List[str]:
        return [file for file in self.codes_and_outputs['data_analysis'].created_files.get_created_content_files()
                if file.startswith('tbl_') or file.startswith('fig_')]

    def get_number_of_created_dfs(self) -> int:
        return len(self.get_created_dfs())

    def get_latex_displayitems(self, view_purpose: ViewPurpose = ViewPurpose.PRODUCT) -> Dict[str, List[str]]:
        """
        Return the tables.
        """
        return {'results': [
            content for file, content
            in self.codes_and_outputs[
                'data_to_latex'].created_files.get_created_content_files_to_pretty_contents(view_purpose).items()
            if file.endswith('.pkl')]}

    def get_all_latex_tables(self, view_purpose: ViewPurpose) -> List[str]:
        """
        Return the tables from all sections.
        """
        return [table for tables in self.get_latex_displayitems(view_purpose).values() for table in tables]

    @property
    def all_file_descriptions(self) -> DataFileDescriptions:
        """
        Return the description of all files.
        """
        desc = DataFileDescriptions.from_other(self.data_file_descriptions)
        for code_and_output in self.codes_and_outputs.values():
            if code_and_output.description_of_created_files is not None:
                desc += code_and_output.description_of_created_files
            else:
                desc += [DataFileDescription(file_path=created_file)
                         for created_file in code_and_output.created_files.get_created_data_files()]
        desc.data_folder = self.data_file_descriptions.data_folder
        return desc

    def get_file_headers(self, code_step: str):
        """
        Return the file headers of a given code_step.
        """
        code_and_output = self.codes_and_outputs[code_step]
        created_files = code_and_output.created_files.get_created_data_files()
        if not created_files:
            return None
        return DataFileDescriptions(
            [DataFileDescription(file_path=created_file) for created_file in created_files],
            data_folder=self.data_file_descriptions.data_folder)

    def get_paper_sections_and_citations(self, remove_hyperlinks: bool = False,
                                         format_num_command: Optional[bool] = False,
                                         ) -> Dict[str, Tuple[str, Set[Citation]]]:
        """
        Like paper_sections_and_optional_citations, but adding empty citations to sections without citations.
        remove_hyperlinks: whether to remove the hyperlinks in the latex sections.
        format_num_command: whether to format the \num{} commands in the latex sections:
            - True, replace the \num{} commands with their values.
            - None, keep the \num{} commands, but remove the explanation.
            - False, keep the \num{} commands.
            format_num_command is only effective with remove_hyperlinks=True.
        """
        section_names_to_sections_and_citations = {}
        for section_name, section_and_optional_citations in self.paper_sections_and_optional_citations.items():
            if isinstance(section_and_optional_citations, str):
                section = section_and_optional_citations
                citations = set()
            else:
                section, citations = section_and_optional_citations
            if remove_hyperlinks:
                section = replace_hyperlinks_with_values(section)
                if format_num_command is not False:
                    section = evaluate_latex_num_command(section, just_strip_explanation=format_num_command is None)[0]

            section_names_to_sections_and_citations[section_name] = (section, citations)
        return section_names_to_sections_and_citations

    def get_paper_sections_without_citations(self, remove_hyperlinks: bool = False,
                                             format_num_command: Optional[bool] = False
                                             ) -> Dict[str, str]:
        return {section_name: section
                for section_name, (section, citation) in self.get_paper_sections_and_citations(
                    remove_hyperlinks=remove_hyperlinks, format_num_command=format_num_command).items()}

    def get_all_cited_citations(self) -> NiceList[Citation]:
        """
        Return the citations of the paper.
        """
        citations = ListBasedSet()
        for section_content, section_citations in self.get_paper_sections_and_citations().values():
            citations.update(section_citations)
        return NiceList(citations, separator='\n\n')

    def get_tabled_paper_sections(self, view_purpose: ViewPurpose) -> Dict[str, str]:
        """
        Return the paper sections with tables inserted at the right places.
        """
        latex_displayitems = self.get_latex_displayitems(view_purpose)
        return {section_name: section if section_name not in latex_displayitems
                else add_displayitems_to_paper_section(section, latex_displayitems[section_name])
                for section_name, section in self.get_paper_sections_without_citations().items()}

    def get_title(self) -> str:
        """
        Return the title of the paper.
        """
        latex = self.get_paper_sections_without_citations()['title']
        return extract_latex_section_from_response(latex, 'title', keep_tags=False)

    def get_abstract(self) -> str:
        """
        Return the abstract of the paper.
        """
        latex = self.get_paper_sections_without_citations()['abstract']
        return extract_latex_section_from_response(latex, 'abstract', keep_tags=False)

    def _get_generators(self) -> Dict[str, NameDescriptionStageGenerator]:
        return {
            **super()._get_generators(),

            # DATA
            # ====

            'general_dataset_description': NameDescriptionStageGenerator(
                'Overall Description of the Dataset',
                '{}',
                ScientificStage.DATA,
                lambda: hypertarget_if_referencable_text_product(self.data_file_descriptions.general_description,
                                                                 ViewPurpose.PRODUCT, level=2),
            ),

            'data_file_descriptions': NameDescriptionStageGenerator(
                'Description of the Original Dataset',
                '{}',
                ScientificStage.DATA,
                lambda: self.data_file_descriptions,
            ),

            'data_file_descriptions_no_headers': NameDescriptionStageGenerator(
                'Description of the Original Dataset',
                '{}',
                ScientificStage.DATA,
                lambda: self.data_file_descriptions.pretty_repr(num_lines=0),
            ),

            'data_file_descriptions_no_headers_linked': NameDescriptionStageGenerator(
                'Description of the Original Dataset (with hypertargets)',
                '{}',
                ScientificStage.DATA,
                lambda: self.data_file_descriptions.pretty_repr(num_lines=0,
                                                                view_purpose=ViewPurpose.HYPERTARGET_PRODUCT),
            ),

            'all_file_descriptions': NameDescriptionStageGenerator(
                'Description of the Dataset',
                '{}',
                ScientificStage.DATA,
                lambda: self.all_file_descriptions,
            ),

            # GOAL AND PLAN
            # ==============

            'research_goal': ProductGenerator(
                lambda: self.research_goal,
                {},
            ),

            'hypothesis_testing_plan': ProductGenerator(
                lambda: self.hypothesis_testing_plan,
                {},
            ),

            # LITERATURE SEARCH
            # =================

            'literature_search:{}': ProductGenerator(
                lambda stage: self.literature_search[stage],
                lambda stage: dict(stage=stage, scope=None),
            ),

            'literature_search:{}:{}': ProductGenerator(
                lambda stage, scope: self.literature_search[stage],
                lambda stage, scope: dict(stage=stage, scope=scope),
            ),

            'most_similar_papers': ProductGenerator(
                lambda: self.most_similar_papers,
                {},
            ),

            'novelty_assessment': ProductGenerator(
                lambda: NoveltySummaryProduct(novelty_assessment=self.novelty_assessment,
                                              most_similar_papers=self.most_similar_papers),
                {},
            ),

            # CODE
            # ====

            'codes:{}': NameDescriptionStageGenerator(
                '{code_name} Code',
                'Here is our {code_name} Code:\n```python\n{code}\n```\n',
                lambda code_step: get_code_stage(code_step),
                lambda code_step: {'code': self.codes_and_outputs[code_step].code,
                                   'code_name': self.codes_and_outputs[code_step].name},
            ),

            'outputs:{}': NameDescriptionStageGenerator(
                'Output of the {code_name} Code',
                'Here is the Output of our {code_name} code:\n{output}',
                lambda code_step: get_code_stage(code_step),
                lambda code_step: {
                    'output': self.codes_and_outputs[code_step].created_files.
                    get_created_content_files_and_contents_as_single_str(view_purpose=ViewPurpose.PRODUCT,
                                                                         header_level=3),
                    'code_name': self.codes_and_outputs[code_step].name},
            ),

            'code_explanation:{}': NameDescriptionStageGenerator(
                '{code_name} Code Description',
                'Here is an explanation of our {code_name} code:\n\n{code_explanation}',
                lambda code_step: get_code_stage(code_step),
                lambda code_step: {
                    'code_name': self.codes_and_outputs[code_step].name,
                    'code_explanation': self.codes_and_outputs[code_step].code_explanation},
            ),

            'codes_and_outputs:{}': NameDescriptionStageGenerator(
                '{code_name} Code and Output',
                '{code_description}\n\n{output_description}',
                lambda code_step: get_code_stage(code_step),
                lambda code_step: {
                    'code_name': self.codes_and_outputs[code_step].name,
                    'code_description': self.get_description('codes:' + code_step),
                    'output_description': self.get_description('outputs:' + code_step)},
            ),

            'codes_and_outputs_with_explanations:{}': NameDescriptionStageGenerator(
                '{code_name} Code and Output',
                '{description}',
                lambda code_step: get_code_stage(code_step),
                lambda code_step: {
                    'code_name': self.codes_and_outputs[code_step].name,
                    'description': self.codes_and_outputs[code_step].to_text(with_header=False)},
            ),

            'created_files_content:{}:{}': NameDescriptionStageGenerator(
                'Content of Files Created by the {code_name} Code',
                'Here is the content of {which_files} created by the {code_name} code:\n\n{created_files_content}',
                lambda code_step, filespec: get_code_stage(code_step),
                lambda code_step, filespec: {
                    'created_files_content':
                        self.codes_and_outputs[
                            code_step].created_files.get_created_content_files_and_contents_as_single_str(
                            view_purpose=ViewPurpose.CODE_REVIEW, match_filename=filespec, header_level=3),
                    'which_files': 'all files' if filespec == '*' else f'files "{filespec}"',
                    'code_name': self.codes_and_outputs[code_step].name},
            ),

            'created_files_description:{}': NameDescriptionStageGenerator(
                'Description of Files Created by the {code_name} Code',
                'We can use these files created by the {code_name} code:\n\n{created_files_description}',
                lambda code_step: get_code_stage(code_step),
                lambda code_step: {
                    'created_files_description': DataFileDescriptions(
                        self.data_file_descriptions + self.codes_and_outputs[code_step].description_of_created_files,
                        data_folder=self.codes_and_outputs[code_step].description_of_created_files.data_folder)
                    if self.codes_and_outputs[code_step].description_of_created_files is not None else None,
                    'code_name': self.codes_and_outputs[code_step].name},
            ),

            'created_files_headers:{}': NameDescriptionStageGenerator(
                'Headers of Files Created by the {code_name} Code',
                'Here are the headers of the files created by the {code_name} code:\n\n{created_files_headers}',
                lambda code_step: get_code_stage(code_step),
                lambda code_step: {
                    'created_files_headers': self.get_file_headers(code_step),
                    'code_name': self.codes_and_outputs[code_step].name},
            ),

            # WRITING
            # =======

            'title_and_abstract_first': NameDescriptionStageGenerator(
                'Title and Abstract (initial draft)',
                "```latex\n{}\n\n{}```",
                ScientificStage.INTERPRETATION,
                lambda: (self.get_paper_sections_without_citations()['title'],
                         self.get_paper_sections_without_citations()['abstract']),
            ),

            'title_and_abstract': NameDescriptionStageGenerator(
                'Title and Abstract',
                "```latex\n{}\n\n{}```",
                ScientificStage.WRITING_TITLE_AND_ABSTRACT,
                lambda: (self.get_paper_sections_without_citations()['title'],
                         self.get_paper_sections_without_citations()['abstract']),
            ),

            'paper_sections:{}': NameDescriptionStageGenerator(
                '{section_name} Section of the Paper',
                '```latex\n{content}\n```',
                lambda section_name: SECTION_NAMES_TO_WRITING_STAGES[section_name],
                lambda section_name: {'section_name': section_name.title(),
                                      'content': self.get_paper_sections_without_citations(
                                          remove_hyperlinks=True, format_num_command=None)[section_name],
                                      },
            ),

            'latex_displayitems': NameDescriptionStageGenerator(
                'Displayitems of the Paper',
                'Here are the displayitems created by our data analysis code '
                '(figure/table latex representations of the df_?.pkl dataframes):\n\n{}',
                ScientificStage.DISPLAYITEMS,
                lambda: None if not self.get_all_latex_tables(ViewPurpose.PRODUCT) else
                '\n\n'.join([f'- "{get_displayitem_caption(table, first_line_only=True)}":\n\n'
                             f'{table}'
                             for table in self.get_all_latex_tables(ViewPurpose.PRODUCT)]),
            ),

            'latex_displayitems_linked': NameDescriptionStageGenerator(
                'Displayitems of the Paper with hypertargets',
                'Here are the displayitems created by our data analysis code '
                '(figure/table latex representations of the df_?.pkl dataframes, with hypertargets):\n\n{}',
                ScientificStage.DISPLAYITEMS,
                lambda: None if not self.get_all_latex_tables(ViewPurpose.HYPERTARGET_PRODUCT) else
                '\n\n'.join([f'- "{get_displayitem_caption(table, first_line_only=True)}":\n\n'
                             f'{table}'
                             for table in self.get_all_latex_tables(ViewPurpose.HYPERTARGET_PRODUCT)]),
            ),

            'additional_results': NameDescriptionStageGenerator(
                'Additional Results (additional_results.pkl)',
                'Here are some additional numeric values that may be helpful in writing the paper:\n\n{}',
                ScientificStage.INTERPRETATION,
                lambda: self.codes_and_outputs[
                    'data_analysis'].created_files.get_created_content_files_to_pretty_contents(
                    view_purpose=ViewPurpose.PRODUCT, header_level=3)['additional_results.pkl'],
            ),

            'additional_results_linked': NameDescriptionStageGenerator(
                'Additional Results (additional_results.pkl) with hypertargets',
                'Here are some additional numeric values that may be helpful in writing the paper:\n\n{}',
                ScientificStage.INTERPRETATION,
                lambda: self.codes_and_outputs[
                    'data_analysis'].created_files.get_created_content_files_to_pretty_contents(
                    view_purpose=ViewPurpose.HYPERTARGET_PRODUCT, header_level=3)['additional_results.pkl'],
            ),
        }
