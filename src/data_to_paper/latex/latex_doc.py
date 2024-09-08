import re
from dataclasses import dataclass, field
from functools import partial
from typing import List, Optional, Dict, Union, Iterable, Collection

from data_to_paper.latex import save_latex_and_compile_to_pdf
from data_to_paper.latex.clean_latex import process_latex_text_and_math
from data_to_paper.latex.latex_to_pdf import evaluate_latex_num_command

from data_to_paper.servers.custom_types import Citation
from data_to_paper.utils import dedent_triple_quote_str

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
    '{sectsty}',
)

DEFAULT_INITIATION_COMMANDS = (r"""
% Default fixed font does not support bold face
\DeclareFixedFont{\ttb}{T1}{txtt}{bx}{n}{12} % for bold
\DeclareFixedFont{\ttm}{T1}{txtt}{m}{n}{12}  % for normal

% Custom colors
\usepackage{color}
\definecolor{deepblue}{rgb}{0,0,0.5}
\definecolor{deepred}{rgb}{0.6,0,0}
\definecolor{deepgreen}{rgb}{0,0.5,0}
\definecolor{cyan}{rgb}{0.0,0.6,0.6}
\definecolor{gray}{rgb}{0.5,0.5,0.5}

% Python style for highlighting
\newcommand\pythonstyle{\lstset{
language=Python,
basicstyle=\ttfamily\footnotesize,
morekeywords={self, import, as, from, if, for, while},              % Add keywords here
keywordstyle=\color{deepblue},
stringstyle=\color{deepred},
commentstyle=\color{cyan},
breaklines=true,
escapeinside={(*@}{@*)},            % Define escape delimiters
postbreak=\mbox{\textcolor{deepgreen}{$\hookrightarrow$}\space},
showstringspaces=false
}}


% Python environment
\lstnewenvironment{python}[1][]
{
\pythonstyle
\lstset{#1}
}
{}

% Python for external files
\newcommand\pythonexternal[2][]{{
\pythonstyle
\lstinputlisting[#1]{#2}}}

% Python for inline
\newcommand\pythoninline[1]{{\pythonstyle\lstinline!#1!}}


% Code output style for highlighting
\newcommand\outputstyle{\lstset{
    language=,
    basicstyle=\ttfamily\footnotesize\color{gray},
    breaklines=true,
    showstringspaces=false,
    escapeinside={(*@}{@*)},            % Define escape delimiters
}}

% Code output environment
\lstnewenvironment{codeoutput}[1][]
{
    \outputstyle
    \lstset{#1}
}
{}

""",
)  # noqa

START_APPENDIX = r"""
\clearpage
\appendix
"""

CITATION_TEMPLATE = r"""
\bibliographystyle{unsrt}
\bibliography{citations}
"""


def replace_scientific_exponent_with_latex(text, with_dollar_signs=True):
    def replace(match):
        base, exponent = match.groups()
        exponent = int(exponent)  # to remove leading zeros
        if base.startswith('-') or base.startswith('+'):
            sign = base[0]
            base = base[1:]
        else:
            sign = ''
        if base == '1':
            s = r'{}10^{{{}}}'.format(sign, exponent)
        else:
            s = r'{}{}\ 10^{{{}}}'.format(sign, base, exponent)
        if with_dollar_signs:
            s = '$' + s + '$'
        return s

    return re.sub(pattern=r'([+-]?[\d.]+)e([+-]?\d+)', repl=replace, string=text)


def get_tabular_block(latex_table: str) -> str:
    """
    Extract the tabular block of the table.
    """
    return re.search(pattern=r'\\begin{tabular}.*\n(.*)\\end{tabular}', string=latex_table, flags=re.DOTALL).group(0)


@dataclass
class LatexDocument:
    """
    A class for creating latex documents and compiling them to pdf.
    """

    kind: str = 'article'
    fontsize: int = 11

    section_heading_fontsize: str = 'Large'
    subsection_heading_fontsize: str = 'normalsize'
    subsubsection_heading_fontsize: str = 'normalsize'
    initiation_commands: List[str] = field(default_factory=lambda: list(DEFAULT_INITIATION_COMMANDS))

    section_numbering: bool = False
    subsection_numbering: bool = False
    subsubsection_numbering: bool = False

    replace_scientific_exponents: bool = True

    author: str = 'data-to-paper'
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

        if not self.subsubsection_numbering:
            section = section.replace(r'\subsubsection{', r'\subsubsection*{')
        else:
            section = section.replace(r'\subsubsection*{', r'\subsubsection{')

        if not self.allow_table_tilde:
            section = section.replace(r'Table\textasciitilde', r'Table ').replace(r'Table \textasciitilde', r'Table ')

        section = evaluate_latex_num_command(section)[0]

        if self.replace_scientific_exponents:
            section = process_latex_text_and_math(
                section,
                process_text=partial(replace_scientific_exponent_with_latex, with_dollar_signs=True),
                process_math=partial(replace_scientific_exponent_with_latex, with_dollar_signs=False),
            )

        return section

    def get_document(self,
                     content: Optional[Union[str, Iterable[str], Dict[Optional[str], str]]] = None,
                     title: Optional[str] = None,
                     abstract: Optional[str] = None,
                     appendix: Optional[str] = None,
                     author: Optional[str] = None,
                     references: Collection[Citation] = None,
                     format_cite: bool = True,
                     add_before_document: Optional[str] = None,
                     file_stem: str = None,
                     output_directory: Optional[str] = None,
                     raise_on_too_wide: bool = True,
                     ) -> (str, str):
        """
        Return the latex document as a string.

        If `file_stem` is given, save the document to a file and compile it to pdf.

        If `output_directory` is given, save the document to that directory.

        If `output_directory` is None:
            compile to pdf but do not save (checking for compilation errors).
            `LatexCompilationError` is raised if there are errors.
        """

        if isinstance(content, dict):
            if 'title' in content:
                title = content.pop('title')
            if 'abstract' in content:
                abstract = content.pop('abstract')

        # Build the document:
        s = ''
        s += r"\documentclass[{fontsize}pt]{{{kind}}}".format(kind=self.kind, fontsize=self.fontsize) + '\n'
        s += '\n'.join([r'\usepackage' + package for package in self.packages]) + '\n'

        s += '\\sectionfont{\\' + self.section_heading_fontsize + '}\n'
        s += '\\subsectionfont{\\' + self.subsection_heading_fontsize + '}\n'
        s += '\\subsubsectionfont{\\' + self.subsubsection_heading_fontsize + '}\n'

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

        # Add before document:
        if add_before_document is not None:
            s += add_before_document + '\n'

        # Begin document:
        s += r'\begin{document}' + '\n'
        if title is not None:
            s += r'\maketitle' + '\n'

        # Abstract:
        if abstract is not None and not (abstract.startswith(r'\abstract') or abstract.startswith(r'\begin{abstract}')):
            abstract = r'\begin{abstract}' + abstract + r'\end{abstract}'
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
        elif content is None:
            all_sections = ''
        else:
            raise TypeError(f'content must be str, Iterable[str] or Dict[str, str], not {type(content)}')

        s += self._style_section(all_sections)

        # References:
        if references:
            s += CITATION_TEMPLATE + '\n'

        # Appendix:
        if appendix is not None:
            s += START_APPENDIX + '\n'
            s += appendix + '\n\n'

        # End document:
        s += r'\end{document}' + '\n'

        # Save and compile:
        pdf_output = save_latex_and_compile_to_pdf(s, file_stem=file_stem, output_directory=output_directory,
                                                   references=references, raise_on_too_wide=raise_on_too_wide,
                                                   format_cite=format_cite)
        return s, pdf_output

    def compile_table(self, latex_table: str, file_stem: str = None, output_directory: Optional[str] = None) -> float:
        """
        Compile a latex table to pdf and return the width of the tabular part of the table,
        expressed as fraction of the page margin width.
        """

        lrbox_table = dedent_triple_quote_str(r"""
            % Define the save box within the document block
            \newsavebox{\mytablebox} % Create a box to store the table

            % Save only the tabular part of table in the \mytablebox without typesetting it:
            \begin{lrbox}{\mytablebox}
              <tabular>%
            \end{lrbox}

            % Typeset the entire table:
            <table>

            % Print the width of the tabular part of the table and the width of the page margin to the log file
            \typeout{Table width: \the\wd\mytablebox}
            \typeout{Page margin width: \the\textwidth}
            """).replace('<tabular>', get_tabular_block(latex_table)).replace('<table>', latex_table)

        _, pdf_output = self.get_document(content=lrbox_table,
                                          file_stem=file_stem,
                                          output_directory=output_directory,
                                          raise_on_too_wide=False,
                                          format_cite=False,
                                          )

        table_width = re.findall(pattern=r'Table width: (\d+\.\d+)pt', string=pdf_output)[0]
        marging_width = re.findall(pattern=r'Page margin width: (\d+\.\d+)pt', string=pdf_output)[0]
        return float(table_width) / float(marging_width)
