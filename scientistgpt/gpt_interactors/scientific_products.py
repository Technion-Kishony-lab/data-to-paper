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
    abstract: Optional[str] = None
    title: Optional[str] = None
    introduction: Optional[str] = None
    methods: Optional[str] = None
    results: Optional[str] = None
    discussion: Optional[str] = None
    conclusion: Optional[str] = None
