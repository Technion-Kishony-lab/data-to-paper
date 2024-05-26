from dataclasses import dataclass
from typing import Tuple, List, Type

from data_to_paper.base_steps import DebuggerConverser
from data_to_paper.research_types.hypothesis_testing.scientific_products import ScientificProducts
from data_to_paper.run_gpt_code.code_runner import CodeRunner

from data_to_paper.code_and_output_files.code_and_output import CodeAndOutput
from data_to_paper.run_gpt_code.run_issues import CodeProblem, RunIssue


@dataclass
class UtilsCodeRunner(CodeRunner):
    def _modify_code(self, code: str) -> Tuple[str, int]:
        """
        Modify the extracted code before running it.
        """
        modified_code, lines_added = super()._modify_code(code)
        modified_code = code.replace(
            'from my_utils',
            'from data_to_paper.research_types.hypothesis_testing.coding.utils_modified_for_gpt_use')
        return modified_code, lines_added


@dataclass
class LatexTablesDebuggerConverser(DebuggerConverser):
    products: ScientificProducts = None
    code_runner_cls: Type[CodeRunner] = UtilsCodeRunner

    def _get_issues_for_created_output_files(self, code_and_output: CodeAndOutput, contexts) -> List[RunIssue]:
        num_created_pkl_df_files = self.products.get_number_of_created_dfs()
        created_tex_files = code_and_output.created_files.get_created_content_files()
        if len(created_tex_files) < num_created_pkl_df_files:
            return [RunIssue(
                category='Missing output files',
                issue=f"We have {num_created_pkl_df_files} df_?.pkl files, but only "
                      f"{len(created_tex_files)} tex files were created.",
                instructions=f"Please create a tex file for each table.",
                code_problem=CodeProblem.OutputFileContentLevelA,
            )]
        return super()._get_issues_for_created_output_files(code_and_output, contexts)
