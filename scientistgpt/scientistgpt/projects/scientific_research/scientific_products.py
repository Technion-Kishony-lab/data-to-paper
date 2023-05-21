from dataclasses import dataclass, field
from typing import Optional, Dict, Tuple, Set, List

from scientistgpt.projects.scientific_research.scientific_stage import ScientificStage
from scientistgpt.run_gpt_code.types import CodeAndOutput
from scientistgpt.utils.nice_list import NiceList
from scientistgpt.base_steps.types import DataFileDescriptions, Products, NameDescriptionStageGenerator
from scientistgpt.servers.crossref import CrossrefCitation


@dataclass
class ScientificProducts(Products):
    """
    Contains the different scientific outcomes of the research.
    These outcomes are gradually populated, where in each step we get a new product based on previous products.
    """
    data_file_descriptions: DataFileDescriptions = field(default_factory=DataFileDescriptions)
    data_exploration_code_and_output: CodeAndOutput = field(default_factory=CodeAndOutput)
    research_goal: Optional[str] = None
    analysis_plan: Optional[str] = None
    data_analysis_code_and_output: CodeAndOutput = None
    tables: Dict[str, Dict[str, str]] = None
    numeric_values: Dict[str, str] = None
    results_summary: Optional[str] = None
    paper_sections: Dict[str, str] = field(default_factory=dict)
    cited_paper_sections_and_citations: Dict[str, Tuple[str, Set[CrossrefCitation]]] = field(default_factory=dict)
    ready_to_be_tabled_paper_sections: Dict[str, str] = field(default_factory=dict)

    @property
    def citations(self) -> NiceList[CrossrefCitation]:
        """
        Return the citations of the paper.
        """
        citations = set()
        for section_content, section_citations in self.cited_paper_sections_and_citations.values():
            citations.update(section_citations)
        return NiceList(citations, separator='\n\n')

    @property
    def cited_paper_sections(self) -> Dict[str, str]:
        """
        Return the actual cited paper sections.
        """
        return {section_name: section_content
                for section_name, (section_content, _) in self.cited_paper_sections_and_citations.items()}

    @property
    def most_updated_paper_sections(self) -> Dict[str, str]:
        section_names_to_content = {}
        for section_name, section in self.paper_sections.items():
            if section_name in self.cited_paper_sections:
                section = self.cited_paper_sections[section_name]
            if section_name in self.tabled_paper_sections:
                section = self.tabled_paper_sections[section_name]
            section_names_to_content[section_name] = section
        return section_names_to_content

    def get_paper(self, product_field: str) -> str:
        """
        Compose the paper from the different paper sections.
        product_field can be one of the following:
            'paper_sections'
            'cited_paper_sections'
            'tabled_paper_sections'
            'most_updated_paper_sections'
        """
        paper_sections = getattr(self, product_field)
        paper = ''
        for section_name, section_content in paper_sections.items():
            paper += f"``{section_name}``\n\n{section_content}\n\n\n"
        return paper

    def _get_generators(self) -> Dict[str, NameDescriptionStageGenerator]:
        return {
            'data_file_descriptions': NameDescriptionStageGenerator(
                'Dataset',
                'DESCRIPTION OF DATASET\n\nWe have the following {}',
                ScientificStage.DATA,
                lambda: self.data_file_descriptions,
            ),

            'data_exploration_code': NameDescriptionStageGenerator(
                'Data Exploration Code',
                'Here is our Data Exploration code:\n```python\n{}\n```\n',
                ScientificStage.EXPLORATION,
                lambda: self.data_exploration_code_and_output.code,
            ),

            'data_exploration_output': NameDescriptionStageGenerator(
                'Output of Data Exploration',
                'Here is the output of our Data Exploration code:\n```\n{}\n```\n',
                ScientificStage.EXPLORATION,
                lambda: self.data_exploration_code_and_output.output,
            ),

            'data_exploration_code_and_output': NameDescriptionStageGenerator(
                'Data Exploration',
                '{}\n\n{}',
                ScientificStage.EXPLORATION,
                lambda: (self['data_exploration_code'].description, self['data_exploration_output'].description),
            ),

            'research_goal': NameDescriptionStageGenerator(
                'Research Goal',
                'Here is our Research Goal\n\n{}',
                ScientificStage.GOAL,
                lambda: self.research_goal,
            ),

            'analysis_plan': NameDescriptionStageGenerator(
                'Data Analysis Plan',
                'Here is our Data Analysis Plan:\n\n{}',
                ScientificStage.PLAN,
                lambda: self.analysis_plan,
            ),

            'data_analysis_code': NameDescriptionStageGenerator(
                'Data Analysis Code',
                'Here is our Data Analysis Code:\n```python\n{}\n```\n',
                ScientificStage.CODE,
                lambda: self.data_analysis_code_and_output.code,
            ),

            'data_analysis_output': NameDescriptionStageGenerator(
                'Output of the Data Analysis Code',
                'Here is the output of our Data Analysis code:\n```\n{}\n```\n',
                ScientificStage.CODE,
                lambda: self.data_analysis_code_and_output.output,
            ),

            'data_analysis_code_and_output': NameDescriptionStageGenerator(
                'Data Analysis Code and Output',
                '{}\n\n{}',
                ScientificStage.CODE,
                lambda: (self["data_analysis_code"].description, self["data_analysis_output"].description)
            ),

            'results_summary': NameDescriptionStageGenerator(
                'Results Summary',
                'Here is our Results Summary:\n\n{}',
                ScientificStage.INTERPRETATION,
                lambda: self.results_summary,
            ),

            'title_and_abstract': NameDescriptionStageGenerator(
                'Title and Abstract',
                "Here are the title and abstract of the paper:\n\n{}\n\n{}",
                ScientificStage.WRITING,
                lambda: (self.paper_sections['title'], self.paper_sections['abstract']),
            ),

            'paper_sections': NameDescriptionStageGenerator(
                'Paper Sections',
                '{}',
                ScientificStage.WRITING,
                lambda: self.get_paper("paper_sections")
            ),

            'cited_paper_sections_and_citations': NameDescriptionStageGenerator(
                'Cited Paper Sections and Citations',
                '{}\n\n\n``Citations``\n\n{}',
                ScientificStage.CITATIONS,
                lambda: (self.get_paper("cited_paper_sections"), self.citations),
            ),

            'tabled_paper_sections': NameDescriptionStageGenerator(
                'Paper Sections with Tables',
                '{}',
                ScientificStage.TABLES,
                lambda: self.get_paper("tabled_paper_sections")
            ),

            'most_updated_paper_sections': NameDescriptionStageGenerator(
                'Most Updated Paper Sections',
                '{}',
                ScientificStage.WRITING,
                lambda: self.get_paper("most_updated_paper_sections")
            ),

            'paper_sections:{}': NameDescriptionStageGenerator(
                'The {section_name} Section of the Paper',
                'Here is the {section_name} section of the paper:\n\n{content}',
                ScientificStage.WRITING,
                lambda section_name: {'section_name': section_name.title(),
                                      'content': self.paper_sections[section_name],
                                      },
            ),

            'cited_paper_sections_and_citations:{}': NameDescriptionStageGenerator(
                'The {section_name} Section of the Paper with Citations',
                'Here is the cited {section_name} section of the paper:\n\n{content}\n\n``Citations``\n\n{citations}',
                ScientificStage.CITATIONS,
                lambda section_name: {'section_name': section_name.title(),
                                      'content': self.cited_paper_sections[section_name],
                                      'citations': self.citations[section_name],
                                      },
            ),

            'tabled_paper_sections:{}': NameDescriptionStageGenerator(
                'The {section_name} Section of the Paper with Tables',
                'Here is the {section_name} section of the paper with tables:\n\n{content}',
                ScientificStage.TABLES,
                lambda section_name: {'section_name': section_name.title(),
                                      'content': self.tabled_paper_sections[section_name],
                                      },
            ),

            'most_updated_paper_sections:{}': NameDescriptionStageGenerator(
                'The most-updated {section_name} Section of the Paper',
                'Here is the most-updated {section_name} section of the paper:\n\n{content}',
                ScientificStage.TABLES,
                lambda section_name: {'section_name': section_name.title(),
                                      'content': self.most_updated_paper_sections[section_name],
                                      },
            ),

            'tables': NameDescriptionStageGenerator(
                'The Tables of the Paper',
                'Here are the tables of the paper:\n\n{}',
                ScientificStage.TABLES,
                lambda: NiceList([f"Table {i}, {table_name}:\n\n {table_content}"
                                  for i, (table_name, table_content) in enumerate(self.tables.items())],
                                 separator='\n\n'), ),

            'numeric_values': NameDescriptionStageGenerator(
                'The Numeric Values of the Paper',
                'Here are the numeric values of the paper:\n\n{}',
                ScientificStage.INTERPRETATION,
                lambda: NiceList([f"Numeric Value {i}, {numeric_value_name}:\n\n {numeric_value_content}"
                                  for i, (numeric_value_name, numeric_value_content) in
                                  enumerate(self.numeric_values.items())], separator='\n\n'), ),

            'tables_and_numeric_values': NameDescriptionStageGenerator(
                'The Tables and Numeric Values of the Paper',
                '{tables}\n\n{numeric_values}',
                ScientificStage.INTERPRETATION,
                lambda: {'tables': self['tables'].description,
                         'numeric_values': self['numeric_values'].description,
                         },
            ),
        }
