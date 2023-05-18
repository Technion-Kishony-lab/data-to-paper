from dataclasses import dataclass, field
from typing import Optional, Dict, Tuple, Set, ClassVar

from scientistgpt.projects.scientific_research.scientific_stage import ScientificStage
from scientistgpt.run_gpt_code.types import CodeAndOutput
from scientistgpt.utils.text_utils import NiceList
from scientistgpt.base_steps.types import DataFileDescriptions, Products
from scientistgpt.servers.crossref import CrossrefCitation


@dataclass
class ScientificProducts(Products):
    """
    Contains the different scientific outcomes of the research.
    These outcomes are gradually populated, where in each step we get a new product based on previous products.
    """
    data_file_descriptions: DataFileDescriptions = None
    research_goal: Optional[str] = None
    analysis_plan: Optional[str] = None
    code_and_output: CodeAndOutput = None
    results_summary: Optional[str] = None
    paper_sections: Dict[str, str] = field(default_factory=dict)
    cited_paper_sections: Dict[str, Tuple[str, Set[CrossrefCitation]]] = field(default_factory=dict)
    tabled_paper_sections: Dict[str, str] = field(default_factory=dict)

    @property
    def citations(self) -> NiceList[CrossrefCitation]:
        """
        Return the citations of the paper.
        """
        citations = set()
        for section_content, section_citations in self.cited_paper_sections.values():
            citations.update(section_citations)
        return NiceList(citations, separator='\n\n', last_separator=None)

    @property
    def actual_cited_paper_sections(self) -> Dict[str, str]:
        """
        Return the actual cited paper sections.
        """
        return {section_name: section_content
                for section_name, (section_content, _) in self.cited_paper_sections.items()}

    @property
    def most_updated_paper_sections(self) -> Dict[str, str]:
        section_names_to_content = {}
        for section_name, section in self.paper_sections.items():
            if section_name in self.actual_cited_paper_sections:
                section = self.actual_cited_paper_sections[section_name]
            if section_name in self.tabled_paper_sections:
                section = self.tabled_paper_sections[section_name]
            section_names_to_content[section_name] = section
        return section_names_to_content

    FIELDS_TO_NAME_STAGE_DESCRIPTION: ClassVar[Dict[str, Tuple[str, ScientificStage, str]]] = {
        'data_file_descriptions': (
            'Dataset',
            ScientificStage.DATA,
            'DESCRIPTION OF DATASET\n\nWe have the following {}',
        ),

        'research_goal': (
            'Research Goal',
            ScientificStage.GOAL,
            'DESCRIPTION OF OUR RESEARCH GOAL.\n\n{}',
        ),

        'analysis_plan': (
            'Data Analysis Plan',
            ScientificStage.PLAN,
            'Here is our data analysis plan:\n\n{}',
        ),

        'code': (
            'code',
            ScientificStage.CODE,
            'Here is our code:\n\n```python\n{self.code_and_output.code}\n```\n',
        ),

        'code_output': (
            'Output of the Code',
            ScientificStage.CODE,
            'Here is our code:\n\n```python\n{self.code_and_output.code}\n```\n'
            '```\n{self.code_and_output.output}\n```\n',
        ),

        'code_and_output': (
            'Code and Output',
            ScientificStage.CODE,
            '{self["code"]}\n\n{self["code_output"][2]}',
        ),

        'results_summary': (
            'Results Summary',
            ScientificStage.INTERPRETATION,
            'Here is a summary of our results:\n\n{}',
        ),

        'title_and_abstract': (
            'Title and Abstract',
            ScientificStage.WRITING,
            "Here are the title and abstract of the paper:\n\n"
            "{self.paper_sections['title']}\n\n"
            "{self.paper_sections['abstract']}",
        ),

        'paper_sections': (
            'Paper Sections',
            ScientificStage.WRITING,
            '{get_paper(self.paper_sections)}',
        ),

        'cited_paper_sections': (
            'Cited Paper Sections and Citations',
            ScientificStage.CITATIONS,
            '{get_paper(self.actual_cited_paper_sections)}\n\n\n``Citations``\n\n{self.citations}'
        ),

        'tabled_paper_sections': (
            'Paper Sections with Tables',
            ScientificStage.TABLES,
            'get_paper(self.tabled_paper_sections)',
        ),

        'most_updated_paper_sections': (
            'Most Updated Paper Sections',
            ScientificStage.WRITING,
            '{get_paper(self.most_updated_paper_sections)}',
        ),

        'paper_sections:{xxx}': (
            'The {"{xxx}".title()} Section of the Paper',
            ScientificStage.WRITING,
            'Here is the {"{xxx}".title()} section of the paper:\n\n{"{self.paper_sections["{xxx}"]}"}'
        ),

        'cited_paper_sections:{xxx}': (
            'The {"{xxx}".title()} Section of the Paper with Citations',
            ScientificStage.CITATIONS,
            'Here is the cited {"{xxx}".title()} section of the paper:\n\n'
            '{self.cited_paper_sections["{xxx}"][0]}\n\n'
            '``Citations``\n\n'
            '{"{NiceList(self.cited_paper_sections["{xxx}"][1], separator="\\n\\n", last_separator=None)}"}'
        ),

        'tabled_paper_sections:{xxx}': (
            'The {"{xxx}".title()} Section of the Paper with Tables',
            ScientificStage.TABLES,
            'Here is the {"{xxx}".title()} section of the paper with tables:\n\n'
            '{"{self.tabled_paper_sections["{xxx}"]}"}'
        ),

        'most_updated_paper_sections:{xxx}': (
            'The most-updated {"{xxx}".title()} Section of the Paper',
            ScientificStage.TABLES,
            'Here is the most-updated {"{xxx}".title()} section of the paper:\n\n'
            '{"{self.most_updated_paper_sections["{xxx}"]}"}'
        ),
    }
