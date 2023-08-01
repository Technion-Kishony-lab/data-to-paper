from dataclasses import dataclass
from typing import Optional, Tuple, List

from data_to_paper.base_steps import DebuggerConverser, CheckLatexCompilation
from data_to_paper.utils import dedent_triple_quote_str

from data_to_paper.run_gpt_code.types import ContentOutputFileRequirement, RunIssue, CodeProblem


@dataclass
class TablesDebuggerConverser(CheckLatexCompilation, DebuggerConverser):
    tolerance_for_too_wide_in_pts: Optional[float] = 25.
    headers_required_in_code: Tuple[str, ...] = (
        '# IMPORT',
        '# LOAD DATA',
        '# PREPROCESSING',
        '# ANALYSIS',
        '# PREPARE TABLES',
        '# OUTPUT TEXT FILE',
    )

    def _get_issues_for_static_code_check(self, code: str) -> List[RunIssue]:
        issues = super()._get_issues_for_static_code_check(code)

        for un_allowed_func in ['to_latex', 'as_latex']:
            if un_allowed_func + '(' in code:
                issues.append(RunIssue(
                    issue=f"It seems like you are using the `{un_allowed_func}` method.",
                    instructions=f"Please use the `to_latex_with_note` method instead.",
                    comment='Unallowed method used',
                    code_problem=CodeProblem.StaticCheck,
                ))

        return issues

    def _get_issues_for_output_file_content(self, requirement: ContentOutputFileRequirement,
                                            filename: str, content: str) -> List[RunIssue]:
        """
        We try to compile the table, and if it fails, we return an issue.
        """
        if not requirement.filename.endswith('.tex'):
            return super()._get_issues_for_output_file_content(requirement, filename, content)

        # We now check that the content of the file compiles to a pdf:
        e = self._check_latex_compilation(content, filename, is_table=True)

        if not isinstance(e, float):
            issue = RunIssue(
                category='Table pdflatex compilation failure',
                item=filename,
                issue=dedent_triple_quote_str("""
                    Here is the created table:
        
                    ```latex
                    {table}
                    ```
        
                    When trying to compile it using pdflatex, I got the following error:
        
                    {error}
        
                    """).format(filename=filename, table=content, error=e),
                comment='Table compilation failed',
                code_problem=CodeProblem.OutputFileDesignLevelB,
            )
        elif e > 1.1:
            issue = RunIssue(
                category='Table too wide',
                comment='Table too wide',
                item=filename,
                issue=dedent_triple_quote_str("""
                    Here is the created table:
        
                    ```latex
                    {table}
                    ```
                    I tried to compile it, but the table is too wide. 
                    """).format(filename=filename, table=content),
                instructions=dedent_triple_quote_str("""                
                    Please change the code to make the table narrower. Consider any of the following options:
        
                    - Drop unnecessary columns. \
                    Use `to_latex_with_note(df, filename, columns=...)` to select only the columns you need.
        
                    - Rename columns to shorter names. \
                    Replace `to_latex_with_note(df, filename, ...)` with \
                    `to_latex_with_note(df.rename(columns=...), filename, ...)`
        
                    - If the table has the dataframe index, you can rename the index to a shorter names.
                    Replace `to_latex_with_note(df, ...)` with `to_latex_with_note(df.rename(index=...), ...)`
        
                    - Alternatively, consider completely transposing the table. \
                    Replace `to_latex_with_note(df, ...)` with `to_latex_with_note(df.T, ...)`
        
                    IMPORTANT:
                    If you rename the columns or the index, \
                    make sure to use the `note` argument of the `to_latex_with_note` function \
                    to clarify the abbreviations used.
                    """),
                code_problem=CodeProblem.OutputFileContentLevelC,
            )
        else:
            issue = None

        return [issue] if issue is not None else []
