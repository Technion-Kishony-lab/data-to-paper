from dataclasses import dataclass
from functools import partial
from typing import Optional, Tuple, List, Type

from data_to_paper.base_steps import DebuggerConverser, CheckLatexCompilation
from data_to_paper.researches_types.scientific_research.scientific_products import ScientificProducts
from data_to_paper.run_gpt_code.code_runner import CodeRunner

from data_to_paper.run_gpt_code.types import RunIssue, CodeProblem, CodeAndOutput


@dataclass
class UtilsCodeRunner(CodeRunner):
    def _modify_code(self, code: str) -> Tuple[str, int]:
        """
        Modify the extracted code before running it.
        """
        modified_code, lines_added = super()._modify_code(code)
        modified_code = code.replace(
            'from my_utils',
            'from data_to_paper.researches_types.scientific_research.utils_for_gpt_code.utils_modified_for_gpt_use')
        return modified_code, lines_added


@dataclass
class TablesDebuggerConverser(CheckLatexCompilation, DebuggerConverser):
    products: ScientificProducts = None
    code_runner_cls: Type[CodeRunner] = UtilsCodeRunner

    tolerance_for_too_wide_in_pts: Optional[float] = 25.

    def _get_runtime_available_objects(self) -> dict:
        return {'compile_to_pdf_func': partial(self._check_latex_compilation, is_table=True)}

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

    def _get_issues_for_created_output_files(self, code_and_output: CodeAndOutput) -> List[RunIssue]:
        num_created_pkl_table_files = self.products.get_number_of_created_df_tables()
        created_tex_table_files = code_and_output.created_files.get_created_content_files()
        if len(created_tex_table_files) < num_created_pkl_table_files:
            return [RunIssue(
                issue=f"We have {num_created_pkl_table_files} table_?.pkl files, but only "
                      f"{len(created_tex_table_files)} tex files were created.",
                instructions=f"Please create a tex file for each table.",
                code_problem=CodeProblem.OutputFileContentLevelA,
            )]
        return super()._get_issues_for_created_output_files(code_and_output)
