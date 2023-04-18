import dataclasses
from dataclasses import dataclass, field
from typing import Optional, List

from scientistgpt.run_gpt_code.code_runner import CodeAndOutput


@dataclass
class ScientificProducts:
    """
    Contains the different scientific outcomes of the research.
    These outcomes are gradually populated and refined by the ScientistGPT.
    """
    data_description: Optional[str] = None
    goal_description: Optional[str] = None
    analysis_plan: Optional[str] = None
    analysis_codes_and_outputs: List[CodeAndOutput] = field(default_factory=list)
    result_summary: Optional[str] = None
    implications: Optional[str] = None
    limitations: Optional[str] = None


@dataclass
class PaperSections:
    """
    Contains the different sections of a scientific paper.
    """
    abstract: Optional[str] = None
    title: Optional[str] = None
    introduction: Optional[str] = None
    methods: Optional[str] = None
    results: Optional[str] = None
    discussion: Optional[str] = None
    conclusion: Optional[str] = None


SCIENTIFIC_PRODUCT_FIELD_NAMES = [field.name for field in dataclasses.fields(ScientificProducts)]
PAPER_SECTION_FIELD_NAMES = [field.name for field in dataclasses.fields(PaperSections)]
