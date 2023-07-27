from dataclasses import dataclass
from typing import Optional

from data_to_paper.base_steps import DebuggerConverser, CheckLatexCompilation
from data_to_paper.utils import dedent_triple_quote_str

from data_to_paper.run_gpt_code.types import ContentOutputFileRequirement
from data_to_paper.latex.exceptions import TooWideTableOrText
from data_to_paper.latex.tables import get_table_label, get_table_caption, get_table_column_headers, get_table_row_names


@dataclass
class TablesDebuggerConverser(CheckLatexCompilation, DebuggerConverser):
    tolerance_for_too_wide_in_pts: Optional[float] = 25.
    num_tables: Optional[int] = None

    def _check_code_and_respond(self, code: str):
        if not super()._check_code_and_respond(code):
            return False
        if self.num_tables is None:
            return True
        for un_allowed_func in ['to_latex', 'as_latex']:
            if un_allowed_func + '(' in code:
                self.apply_append_user_message(dedent_triple_quote_str(f"""
                    It seems like you are using the `{un_allowed_func}` method.
                    Please rewrite the complete code again so that all tables are created using `to_latex_with_note`.
                    """))
                return False
        return True

    def _check_and_response_to_file_content(self, requirement: ContentOutputFileRequirement,
                                            filename: str, content: str) -> Optional[str]:
        message = super()._check_and_response_to_file_content(requirement, filename, content)
        if message is not None:
            return message
        if not requirement.filename.endswith('.tex'):
            return None
        message = self._get_message_on_table_issues(filename, content)
        if message is None:
            return None
        self._requesting_modifications = True
        return message + dedent_triple_quote_str("""\n
            Please rewrite the complete code again, so that the table is created properly.
            Please return the full complete code again, not just the part that was modified, \
            so that I can just copy-paste and run it.
            """)

    def _get_message_on_table_issues(self, filename: str, content: str) -> Optional[str]:
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
