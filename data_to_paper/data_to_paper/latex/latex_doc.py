from dataclasses import dataclass, field
from typing import List, Optional, Dict, Set, Union, Iterable, Collection

from data_to_paper.latex import save_latex_and_compile_to_pdf
from data_to_paper.servers.types import Citation

DEFAULT_PACKAGES = (
    '[utf8]{inputenc}',
    '{hyperref}',
    '{amsmath}',
    '{booktabs}',
    '{multirow}',
    '{threeparttable}',
    '{fancyvrb}',
    '{color}',
    '{listings}',
    '{minted}',
    '{sectsty}',
)

DEFAULT_INITIATION_COMMANDS = (
    r"""\lstset{
    basicstyle=\ttfamily\footnotesize,
    columns=fullflexible,
    breaklines=true,
    }""",
)

START_APPENDIX = r"""
\clearpage
\appendix
"""

CITATION_TEMPLATE = r"""
\bibliographystyle{unsrt}
\bibliography{citations}
"""


@dataclass
class LatexDocument:
    """
    A class for creating latex documents and compiling them to pdf.
    """

    kind: str = 'article'
    fontsize: str = 11

    section_heading_fontsize: str = 'Large'
    subsection_heading_fontsize: str = 'normalsize'
    initiation_commands: List[str] = field(default_factory=lambda: list(DEFAULT_INITIATION_COMMANDS))

    section_numbering: bool = False
    subsection_numbering: bool = False

    author: str = 'Data to Paper'
    packages: List[str] = field(default_factory=lambda: list(DEFAULT_PACKAGES))

    allow_table_tilde: bool = False

    def _style_section(self, section: str) -> str:
        if not self.section_numbering:
            section = section.replace(r'\section{', r'\section*{')
        else:
            section = section.replace(r'\section*{', r'\section{')
        if not self.subsection_numbering:
            section = section.replace(r'\subsection{', r'\subsection*{')
        else:
            section = section.replace(r'\subsection*{', r'\subsection{')
        if not self.allow_table_tilde:
            section = section.replace(r'Table\textasciitilde', r'Table ').replace(r'Table \textasciitilde', r'Table ')
        return section

    def get_document(self,
                     content: Optional[Union[str, Iterable[str], Dict[Optional[str], str]]] = None,
                     title: Optional[str] = None,
                     abstract: Optional[str] = None,
                     appendix: Optional[str] = None,
                     author: Optional[str] = None,
                     references: Collection[Citation] = None,
                     file_stem: str = None,
                     output_directory: Optional[str] = None,
                     ) -> str:
        """
        Return the latex document as a string.

        If `file_stem` is given, save the document to a file and compile it to pdf.

        If `output_directory` is given, save the document to that directory.

        If `output_directory` is None:
            compile to pdf but do not save (checking for compilation errors).
            `LatexCompilationError` is raised if there are errors.
        """

        # Build the document:
        s = ''
        s += r"\documentclass[{fontsize}pt]{{{kind}}}".format(kind=self.kind, fontsize=self.fontsize) + '\n'
        s += '\n'.join([r'\usepackage' + package for package in self.packages]) + '\n'

        s += '\\sectionfont{\\' + self.section_heading_fontsize + '}\n'
        s += '\\subsectionfont{\\' + self.subsection_heading_fontsize + '}\n'

        s += '\n'.join(self.initiation_commands) + '\n'

        # Define title, author:
        if title is not None and not title.startswith(r'\title'):
            title = r'\title{' + title + '}'
        if title is not None:
            s += title + '\n'

        author = author or self.author
        if author is not None and not author.startswith(r'\author'):
            author = r'\author{' + author + '}'
        if author is not None:
            s += author + '\n'

        # Begin document:
        s += r'\begin{document}' + '\n'
        if title is not None:
            s += r'\maketitle' + '\n'

        # Abstract:
        if abstract is not None and not abstract.startswith(r'\abstract'):
            abstract = r'\abstract{' + abstract + '}'
        if abstract is not None:
            s += abstract + '\n'

        # Content:
        if isinstance(content, str):
            all_sections = content
        elif isinstance(content, dict):
            all_sections = ''
            for section_name, section_content in content.items():
                if not section_content.startswith(r'\section') and not section_content.startswith(r'\subsection') and \
                        section_name is not None:
                    all_sections += r'\section{' + section_name + '}' + '\n'
                all_sections += section_content + '\n\n'
        elif isinstance(content, Iterable):
            all_sections = '\n\n'.join(content) + '\n'
        else:
            raise TypeError(f'content must be str, Iterable[str] or Dict[str, str], not {type(content)}')

        s += self._style_section(all_sections)

        # Appendix:
        if appendix is not None:
            s += START_APPENDIX + '\n'
            s += appendix + '\n\n'

        # References:
        if references:
            s += CITATION_TEMPLATE + '\n'

        # End document:
        s += r'\end{document}' + '\n'

        # Save and compile:
        save_latex_and_compile_to_pdf(s, file_stem=file_stem, output_directory=output_directory, references=references)
        return s
