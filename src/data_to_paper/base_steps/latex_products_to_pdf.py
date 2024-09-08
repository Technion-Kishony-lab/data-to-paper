from dataclasses import dataclass, field
from typing import Dict, List, Optional, Collection

from data_to_paper.servers.custom_types import Citation
from data_to_paper.latex.latex_doc import LatexDocument

from .base_products_to_file import BaseFileProducer


@dataclass
class BaseLatexToPDF(BaseFileProducer):
    """
    Allows creating a pdf based on a LatexDocument template whose sections are populated from the Products.
    """

    latex_document: LatexDocument = field(default_factory=LatexDocument)
    paper_section_names: List[str] = None

    def _get_sections(self) -> Dict[str, str]:
        """
        Return a mapping from section names to their content for all the sections of the paper.
        Should include the 'title' and 'abstract' as keys if the pdf should have a title and abstract.
        """
        return {}

    def _get_references(self) -> Collection[Citation]:
        """
        Return all the references cited.
        """
        return set()

    def _get_appendix(self) -> Optional[str]:
        """
        Return the content of the appendix.
        """
        return None

    def assemble_compile_paper(self) -> str:
        return self.latex_document.get_document(
            content=self._get_sections(),
            appendix=self._get_appendix(),
            references=self._get_references(),
            format_cite=True,
            file_stem=self.output_file_stem,
            output_directory=str(self.output_directory),
            raise_on_too_wide=False,
        )[0]
