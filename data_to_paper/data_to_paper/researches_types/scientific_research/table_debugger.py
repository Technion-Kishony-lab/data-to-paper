from dataclasses import dataclass
from typing import Optional, Tuple, List

from data_to_paper.base_steps import DebuggerConverser, CheckLatexCompilation
from data_to_paper.utils import dedent_triple_quote_str

from data_to_paper.run_gpt_code.types import ContentOutputFileRequirement, RunIssue
from data_to_paper.latex.exceptions import TooWideTableOrText
from data_to_paper.latex.tables import get_table_label, get_table_caption, get_table_column_headers, get_table_row_names


@dataclass
class TablesDebuggerConverser(CheckLatexCompilation, DebuggerConverser):
    tolerance_for_too_wide_in_pts: Optional[float] = 25.
    num_tables: Optional[int] = None
    headers_required_in_code: Tuple[str, ...] = (
        '# IMPORT',
        '# LOAD DATA',
        '# PREPROCESSING',
        '# ANALYSIS',
        '# PREPARE TABLES',
        '# OUTPUT TEXT FILE',
    )

    prompt_to_append_at_end_of_response: str = DebuggerConverser.prompt_to_append_at_end_of_response + \
        dedent_triple_quote_str("""
            Your code must contain the following sections:
            {headers_required_in_code}
        """)

    def _get_issues_for_static_code_check(self, code: str) -> List[RunIssue]:
        issues = super()._get_issues_for_static_code_check(code)
        if self.num_tables is None:
            return issues

        required_strings_not_found = [s for s in self.headers_required_in_code if s.lower() not in code.lower()]
        if len(required_strings_not_found) > 0:
            issues.append(RunIssue(
                issue=dedent_triple_quote_str("""
                Your code must contain the following sections: 
                {headers_required_in_code}.
                But I could not find these headers:
                {required_strings_not_found}.
                Please rewrite the complete code again with all the required sections. 
                """).format(
                    headers_required_in_code=self.headers_required_in_code,
                    required_strings_not_found=required_strings_not_found,
                ),
                comment='Required sections not found',
            ))

        for un_allowed_func in ['to_latex', 'as_latex']:
            if un_allowed_func + '(' in code:
                issues.append(RunIssue(
                    issue=f"It seems like you are using the `{un_allowed_func}` method.",
                    instructions=f"Please use the `to_latex_with_note` method instead.",
                    comment='Unallowed method used',
                ))

        return issues

    def _get_issues_for_output_file_content(self, requirement: ContentOutputFileRequirement,
                                            filename: str, content: str) -> List[RunIssue]:
        issues = super()._get_issues_for_output_file_content(requirement, filename, content)
        if not requirement.filename.endswith('.tex'):
            return issues
        message = self._get_message_on_table_compilation(filename, content)
        if message is None:
            return issues
        issues.append(RunIssue(
            issue=message,
            comment='Table compilation failed',
            rank=6,
        ))
        return issues

    def _get_message_on_table_compilation(self, filename: str, content: str) -> Optional[str]:
        # We now check that the content of the file compiles to a pdf:
        e = self._check_latex_compilation(content, filename)
        if e is not None:
            if isinstance(e, TooWideTableOrText):
                return dedent_triple_quote_str("""
                I ran the code. 
                Here is the table "{filename}" that your code created:

                ```latex
                {table}
                ```

                However, the table is too wide. 

                Please change the code to make the table narrower. Consider any of the following:

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
                """).format(filename=filename, table=content)
            else:
                return dedent_triple_quote_str("""
                I ran the code. 
                Here is the table "{filename}":

                ```latex
                {table}
                ```

                However, when I tried to compile the table, I got the following error:

                {error}

                """).format(filename=filename, table=content, error=e)

        return None
