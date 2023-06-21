from dataclasses import dataclass, field
from functools import reduce
from typing import Optional, Dict, Tuple, Set, List, Union
from operator import or_

import numpy as np

from data_to_paper.conversation.stage import Stage
from data_to_paper.latex.tables import add_tables_to_paper_section
from data_to_paper.projects.scientific_research.cast import ScientificAgent
from data_to_paper.projects.scientific_research.scientific_stage import ScientificStages
from data_to_paper.run_gpt_code.types import CodeAndOutput
from data_to_paper.utils.nice_list import NiceList
from data_to_paper.base_products import DataFileDescriptions, DataFileDescription, Products, \
    NameDescriptionStageGenerator
from data_to_paper.servers.crossref import CrossrefCitation
from data_to_paper.utils.types import ListBasedSet, MemoryDict
from data_to_paper.servers.types import Citation

CODE_STEPS_TO_STAGES_NAMES_AGENTS: Dict[str, Tuple[Stage, str, ScientificAgent]] = {
    'data_exploration': (ScientificStages.EXPLORATION, 'Data Exploration', ScientificAgent.DataExplorer),
    'data_preprocessing': (ScientificStages.PREPROCESSING, 'Data Preprocessing', ScientificAgent.DataPreprocessor),
    'data_analysis': (ScientificStages.CODE, 'Data Analysis', ScientificAgent.Debugger),
}


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


def sort_citations_by_embedding_similarity(citations: List[Citation], embedding: np.ndarray) -> List[Citation]:
    """
    Sort the citations by embedding similarity.
    """
    if not citations:
        return []
    embeddings = np.array([citation['embedding'] for citation in citations])
    similarities = np.dot(embeddings, embedding)
    indices = np.argsort(similarities)[::-1]
    return [citations[i] for i in indices]


@dataclass
class LiteratureSearch:
    scopes_to_queries_to_citations: Dict[str, Dict[str, List[Citation]]] = field(default_factory=dict)
    embedding_target: Optional[np.ndarray] = None

    def get_queries(self, scope: Optional[str] = None) -> List[str]:
        """
        Return the queries in the given scope.
        if scope=None, return all queries.
        """
        if scope is None:
            return sum([self.get_queries(scope) for scope in self.scopes_to_queries_to_citations], [])
        return list(self.scopes_to_queries_to_citations[scope].keys())

    def get_citations(self, scope: Optional[str] = None, query: Optional[str] = None,
                      total: int = None, distribute_evenly: bool = True,
                      sort_by_similarity: bool = False, minimal_influence: int = 0) -> List[Citation]:
        """
        Return the citations in the given scope.
        If embedding_target is not None, sort the citations by embedding similarity.
        If total is not None, return only the first total citations.
        """
        empty = ListBasedSet()
        if scope is None:
            assert query is None
            citations = reduce(
                or_, [self.get_citations(
                    scope=scope,
                    total=total // len(self.scopes_to_queries_to_citations) + 1
                    if distribute_evenly and total is not None else None,
                    minimal_influence=minimal_influence,
                    distribute_evenly=distribute_evenly,
                ) for scope in self.scopes_to_queries_to_citations], empty)
        elif query is None:
            citations = reduce(
                or_, [self.get_citations(
                    scope=scope,
                    query=query,
                    total=total // len(self.scopes_to_queries_to_citations[scope]) + 1
                    if distribute_evenly and total is not None else None,
                    minimal_influence=minimal_influence,
                    distribute_evenly=distribute_evenly,
                ) for query in self.scopes_to_queries_to_citations[scope]], empty)
        else:
            citations = self.scopes_to_queries_to_citations[scope][query]
        citations = list(citations)

        if minimal_influence > 0:
            citations = [citation for citation in citations if citation.influence >= minimal_influence]

        if sort_by_similarity and self.embedding_target is not None:
            citations = sort_citations_by_embedding_similarity(citations, self.embedding_target)
        else:
            citations = sorted(citations, key=lambda citation: citation.search_rank)

        if total is None:
            return citations
        if total < 0:
            return citations[total:]
        else:
            return citations[:total]

    def pretty_repr(self, with_scope_and_queries: bool = False,
                    total: int = None, distribute_evenly: bool = True,
                    sort_by_similarity: bool = False,
                    minimal_influence: int = 0
                    ) -> str:
        s = ''
        for scope in self.scopes_to_queries_to_citations:
            if with_scope_and_queries:
                s += f'Scope: {repr(scope)}\n'
                s += f'Queries: {repr(self.get_queries(scope))}\n\n'
            s += self.pretty_repr_for_scope_and_query(scope=scope,
                                                      total=total // len(self.scopes_to_queries_to_citations) + 1,
                                                      distribute_evenly=distribute_evenly,
                                                      sort_by_similarity=sort_by_similarity,
                                                      minimal_influence=minimal_influence)
        return s

    def pretty_repr_for_scope_and_query(self, scope: str, query: Optional[str] = None,
                                        total: int = None, distribute_evenly: bool = True,
                                        sort_by_similarity: bool = False,
                                        minimal_influence: int = 0) -> str:
        return '\n'.join(
            citation.pretty_repr() for citation
            in self.get_citations(scope=scope, query=query, total=total, distribute_evenly=distribute_evenly,
                                  sort_by_similarity=sort_by_similarity,
                                  minimal_influence=minimal_influence,
                                  ))

    def get_citation(self, bibtex_id: str) -> Optional[Citation]:
        for citation in self.get_citations():
            if citation.bibtex_id == bibtex_id:
                return citation
        return None


@dataclass
class ScientificProducts(Products):
    """
    Contains the different scientific outcomes of the research.
    These outcomes are gradually populated, where in each step we get a new product based on previous products.
    """
    data_file_descriptions: DataFileDescriptions = field(default_factory=DataFileDescriptions)
    codes_and_outputs: Dict[str, CodeAndOutput] = field(default_factory=dict)
    research_goal: Optional[str] = None
    literature_search: Dict[str, LiteratureSearch] = field(default_factory=dict)
    analysis_plan: Optional[str] = None
    hypothesis_testing_plan: Optional[Dict[str, str]] = None
    tables_names: Dict[str, str] = field(default_factory=dict)
    tables: Dict[str, List[str]] = field(default_factory=dict)
    numeric_values: Dict[str, str] = field(default_factory=dict)
    results_summary: Optional[str] = None
    paper_sections_and_optional_citations: Dict[str, Union[str, Tuple[str, Set[Citation]]]] = \
        field(default_factory=MemoryDict)

    @property
    def pretty_hypothesis_testing_plan(self) -> str:
        """
        Return the hypothesis testing plan in a pretty way.
        """
        return '\n'.join(f'Hypothesis: {hypothesis}\nStatistical Test: {test}\n'
                         for hypothesis, test in self.hypothesis_testing_plan.items())

    @property
    def pretty_tables_names(self) -> str:
        """
        Return the tables names in a pretty way.
        """
        return '\n'.join(f'{table_num}: {table_name}' for table_num, table_name in self.tables_names.items())

    def get_tables_names_and_content(self) -> str:
        """
        Return the tables names and content.
        """
        s = 'We are creating a total of {} tables:\n\n'.format(len(self.tables_names))
        tables = self.tables['results']
        for i, (table_num, table_name) in enumerate(self.tables_names.items()):
            s += f'{table_num}: "{table_name}":\n'
            if i < len(tables):
                s += f'{tables[i]}'
            else:
                s += f'Not created yet.'
            s += '\n\n'
        return s

    @property
    def all_tables(self) -> List[str]:
        """
        Return the tables from all sections.
        """
        return [table for tables in self.tables.values() for table in tables]

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
                         for created_file in code_and_output.get_created_files_beside_output_file()]
        desc.data_folder = self.data_file_descriptions.data_folder
        return desc

    def get_file_headers(self, code_step: str):
        """
        Return the file headers of a given code_step.
        """
        code_and_output = self.codes_and_outputs[code_step]
        created_files = code_and_output.get_created_files_beside_output_file()
        if not created_files:
            return None
        return DataFileDescriptions(
            [DataFileDescription(file_path=created_file) for created_file in created_files],
            data_folder=self.data_file_descriptions.data_folder)

    @property
    def paper_sections_and_citations(self) -> Dict[str, Tuple[str, Set[Citation]]]:
        section_names_to_sections_and_citations = {}
        for section_name, section_and_optional_citations in self.paper_sections_and_optional_citations.items():
            if isinstance(section_and_optional_citations, str):
                section_names_to_sections_and_citations[section_name] = (section_and_optional_citations, set())
            else:
                section_names_to_sections_and_citations[section_name] = section_and_optional_citations
        return section_names_to_sections_and_citations

    @property
    def paper_sections_without_citations(self) -> Dict[str, str]:
        return {section_name: section
                for section_name, (section, citation) in self.paper_sections_and_citations.items()}

    @property
    def citations(self) -> NiceList[CrossrefCitation]:
        """
        Return the citations of the paper.
        """
        citations = ListBasedSet()
        for section_content, section_citations in self.paper_sections_and_citations.values():
            citations.update(section_citations)
        return NiceList(citations, separator='\n\n')

    @property
    def tabled_paper_sections(self) -> Dict[str, str]:
        """
        Return the actual tabled paper sections.
        """
        return {section_name: section if section_name not in self.tables
                else add_tables_to_paper_section(section, self.tables[section_name])
                for section_name, section in self.paper_sections_without_citations.items()}

    def get_title(self) -> str:
        """
        Return the title of the paper.
        """
        latex = self.paper_sections_without_citations['title']
        return latex[latex.find('{') + 1:latex.find('}')]

    def get_abstract(self) -> str:
        """
        Return the abstract of the paper.
        """
        latex = self.paper_sections_without_citations['abstract']
        return latex[latex.find('{') + 1:latex.find('}')]

    def _get_generators(self) -> Dict[str, NameDescriptionStageGenerator]:
        return {
            **super()._get_generators(),

            'general_dataset_description': NameDescriptionStageGenerator(
                'Dataset Description',
                'OVERALL DESCRIPTION OF THE DATASET\n\n{}',
                ScientificStages.DATA,
                lambda: self.data_file_descriptions.general_description,
            ),

            'data_file_descriptions': NameDescriptionStageGenerator(
                'Original Dataset',
                'DESCRIPTION OF THE ORIGINAL DATASET\n\n{}',
                ScientificStages.DATA,
                lambda: self.data_file_descriptions,
            ),

            'all_file_descriptions': NameDescriptionStageGenerator(
                'Dataset',
                'DESCRIPTION OF THE DATASET:\n\n{}',
                ScientificStages.DATA,
                lambda: self.all_file_descriptions,
            ),

            'research_goal': NameDescriptionStageGenerator(
                'Research Goal',
                'Here is our Research Goal\n\n{}',
                ScientificStages.GOAL,
                lambda: self.research_goal,
            ),

            'analysis_plan': NameDescriptionStageGenerator(
                'Data Analysis Plan',
                'Here is our Data Analysis Plan:\n\n{}',
                ScientificStages.PLAN,
                lambda: self.analysis_plan,
            ),

            'hypothesis_testing_plan': NameDescriptionStageGenerator(
                'Hypothesis Testing Plan',
                'Here is our Hypothesis Testing Plan:\n\n{}',
                ScientificStages.PLAN,
                lambda: str(self.pretty_hypothesis_testing_plan),
            ),

            'literature_search:{}:{}:{}': NameDescriptionStageGenerator(
                'Literature Search',
                'We did a Literature Search and here are the results:\n\n{}',
                ScientificStages.WRITING,
                lambda step, total, minimal_influence: self.literature_search[step].pretty_repr(
                    total=int(total),
                    minimal_influence=int(minimal_influence),
                    distribute_evenly=True,
                    sort_by_similarity=False,
                ),
            ),

            'literature_search_by_scope:{}:{}:{}:{}': NameDescriptionStageGenerator(
                'Literature Search for {scope}',
                'Here are the results of our Literature Search for {scope}:\n\n{papers}',
                ScientificStages.WRITING,
                lambda step, scope, total, minimal_influence: {
                    'scope': scope.title(),
                    'papers': self.literature_search[step].pretty_repr_for_scope_and_query(
                        scope=scope,
                        total=int(total),
                        minimal_influence=int(minimal_influence),
                        distribute_evenly=True,
                        sort_by_similarity=False,
                    ),
                },
            ),

            'codes:{}': NameDescriptionStageGenerator(
                '{code_name} Code',
                'Here is our {code_name} Code:\n```python\n{code}\n```\n',
                lambda code_step: get_code_stage(code_step),
                lambda code_step: {'code': self.codes_and_outputs[code_step].code,
                                   'code_name': self.codes_and_outputs[code_step].name},
            ),

            'outputs:{}': NameDescriptionStageGenerator(
                'Output of the {code_name} Code',
                'Here is the output of our {code_name} code:\n```output\n{output}\n```\n',
                lambda code_step: get_code_stage(code_step),
                lambda code_step: {'output': self.codes_and_outputs[code_step].output,
                                   'code_name': self.codes_and_outputs[code_step].name},
            ),

            'codes_and_outputs:{}': NameDescriptionStageGenerator(
                '{code_name} Code and Output',
                '{code_description}\n\n{output_description}',
                lambda code_step: get_code_stage(code_step),
                lambda code_step: {
                    'code_name': self.codes_and_outputs[code_step].name,
                    'code_description': self.get_description("codes:" + code_step),
                    'output_description': self.get_description("outputs:" + code_step)},
            ),

            'created_files:{}': NameDescriptionStageGenerator(
                'Files Created by the {code_name} Code',
                'Here are the files created by the {code_name} code:\n\n{created_files}',
                lambda code_step: get_code_stage(code_step),
                lambda code_step: {
                    'created_files': self.codes_and_outputs[code_step].created_files,
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

            'results_summary': NameDescriptionStageGenerator(
                'Results Summary',
                'Here is our Results Summary:\n\n{}',
                ScientificStages.INTERPRETATION,
                lambda: self.results_summary,
            ),

            'title_and_abstract': NameDescriptionStageGenerator(
                'Title and Abstract',
                "Here are the title and abstract of the paper:\n\n{}\n\n{}",
                ScientificStages.WRITING,
                lambda: (self.paper_sections_without_citations['title'],
                         self.paper_sections_without_citations['abstract']),
            ),

            'most_updated_paper': NameDescriptionStageGenerator(
                'Most Updated Draft of the Paper',
                '{}',
                ScientificStages.WRITING,
                lambda: '\n\n'.join(self.tabled_paper_sections.values())
            ),

            'paper_sections:{}': NameDescriptionStageGenerator(
                '{section_name} Section of the Paper',
                'Here is the {section_name} section of the paper:\n\n{content}',
                ScientificStages.WRITING,
                lambda section_name: {'section_name': section_name.title(),
                                      'content': self.paper_sections_without_citations[section_name],
                                      },
            ),

            'tabled_paper_sections:{}': NameDescriptionStageGenerator(
                '{section_name} Section of the Paper with Tables',
                'Here is the {section_name} section of the paper with tables:\n\n{content}',
                ScientificStages.TABLES,
                lambda section_name: {'section_name': section_name.title(),
                                      'content': self.tabled_paper_sections[section_name],
                                      },
            ),

            'tables_names': NameDescriptionStageGenerator(
                'Names of the Tables of the Paper',
                'Here are the Names of the Tables of the Paper:\n\n{}',
                ScientificStages.TABLES,
                lambda: None if not self.tables_names else self.pretty_tables_names,
            ),

            'tables': NameDescriptionStageGenerator(
                'Tables of the Paper',
                'Here are the tables we have for the paper:\n\n{}',
                ScientificStages.TABLES,
                lambda: None if not self.all_tables else
                NiceList([f"Table {i + 1}:\n\n {table}" for i, table in enumerate(self.all_tables)],
                         separator='\n\n'),
            ),

            'tables_and_tables_names': NameDescriptionStageGenerator(
                'Tables of the Paper',
                '{tables}',
                ScientificStages.TABLES,
                lambda: {'tables': self.get_tables_names_and_content()}),

            'numeric_values': NameDescriptionStageGenerator(
                'Numeric Values of the Paper',
                'Here are some key numeric values we can use to write the results of the paper:\n\n{}',
                ScientificStages.INTERPRETATION,
                lambda: None if not self.numeric_values else
                NiceList([f"({i + 1}) {numeric_value_name}:\n {numeric_value_content}"
                          for i, (numeric_value_name, numeric_value_content) in
                          enumerate(self.numeric_values.items())],
                         separator='\n\n'),
            ),

            'tables_and_numeric_values': NameDescriptionStageGenerator(
                'Tables and Numeric Values of the Paper',
                '{tables}\n\n{numeric_values}',
                ScientificStages.INTERPRETATION,
                lambda: {'tables': self.get_description('tables'),
                         'numeric_values': self.get_description('numeric_values')},
            ),
        }
