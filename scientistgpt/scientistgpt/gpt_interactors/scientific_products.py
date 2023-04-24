from dataclasses import dataclass, field, fields
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


SCIENTIFIC_PRODUCT_FIELD_NAMES: List[str] = [field.name for field in fields(ScientificProducts)]
