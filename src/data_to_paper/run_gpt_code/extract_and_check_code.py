import re
from dataclasses import dataclass, field
from typing import Dict, Tuple, List

from data_to_paper.text import line_count, dedent_triple_quote_str
from data_to_paper.run_gpt_code.code_utils import extract_code_from_text
from data_to_paper.run_gpt_code.run_issues import RunIssue, CodeProblem


def get_issue_for_use_of_a_forbidden_function(func: str, suggest_print_to_output: bool) -> RunIssue:
    category = 'Use of un-allowed functions'

    instructions = f"Do not use the function `{func}` in your code."
    if func == 'print':
        instructions += \
            "\nIf you print conditional warning messages, please use `assert` or `raise` instead."
        if suggest_print_to_output:
            instructions += \
                "\nOtherwise, outputs should only be written to the above described output file(s)."
    return RunIssue(
        category=category,
        issue=f"Your code uses the function `{func}`, which is not allowed.",
        instructions=instructions,
        code_problem=CodeProblem.RuntimeError,
        comment=f'Code uses forbidden function {func}',
    )


@dataclass
class CodeExtractor:
    """
    Extract code from a response.
    Keep track of line numbers added in front of the code.
    """

    def _get_raw_code(self, response) -> str:
        """
        Extract the raw code from the response.
        """
        return extract_code_from_text(response)

    def get_modified_code_and_num_added_lines(self, response) -> Tuple[str, int]:
        return self._get_raw_code(response), 0

    def get_issues_for_static_code_check(self, code: str) -> List[RunIssue]:
        return []


@dataclass
class ModifyAndCheckCodeExtractor(CodeExtractor):
    """
    Add additional code in front of the extracted code.
    Make replacements in the extracted code.
    """
    add_in_front_of_code: str = ''
    code_replacements: Dict[str, str] = field(default_factory=dict)

    headers_required_in_code: Tuple[str, ...] = ()
    phrases_required_in_code: Tuple[str, ...] = ()
    un_allowed_phrases: Tuple[str, ...] = ('__name__',)
    suggest_print_to_output: bool = False

    def get_modified_code_and_num_added_lines(self, response) -> Tuple[str, int]:
        """
        Modify the extracted code before running it.
        """
        code, num_added_lines = super().get_modified_code_and_num_added_lines(response)
        code = self.add_in_front_of_code + code
        num_added_lines += line_count(self.add_in_front_of_code)
        for old, new in self.code_replacements.items():
            code = code.replace(old, new)
        return code, num_added_lines

    def get_issues_for_static_code_check(self, code: str) -> List[RunIssue]:
        issues = []
        required_strings_not_found = [s for s in self.headers_required_in_code if s.lower() not in code.lower()]
        if len(required_strings_not_found) > 0:
            issues.append(RunIssue(
                category='Code structure',
                issue=dedent_triple_quote_str("""
                Your code must contain the following sections: 
                {headers_required_in_code}.
                But I could not find these headers:
                {required_strings_not_found}.
                """).format(
                    headers_required_in_code=self.headers_required_in_code,
                    required_strings_not_found=required_strings_not_found,
                ),
                instructions='Please rewrite the complete code again with all the required sections.',
                comment='Required sections not found',
                code_problem=CodeProblem.StaticCheck,
            ))

        # check if code uses `print`:
        if re.search(pattern=r'\bprint\s*\(', string=code):
            issues.append(get_issue_for_use_of_a_forbidden_function('print', self.suggest_print_to_output))

        # check if code has un-allowed keywords:
        for phrase in self.un_allowed_phrases:
            if phrase in code:
                issues.append(RunIssue(
                    category='Un-allowed phrases in code',
                    issue=f"Your code uses `{phrase}`, which is not allowed.",
                    instructions=f"Please rewrite the complete code again without using `{phrase}`.",
                    comment=f'Code uses forbidden phrase.',
                    code_problem=CodeProblem.StaticCheck,
                ))

        # check if code has all required keywords:
        for phrase in self.phrases_required_in_code:
            if phrase not in code:
                issues.append(RunIssue(
                    category='Missing/imperfect commands',
                    issue=f"Your code must explicitly use:\n`{phrase.strip()}`.",
                    comment=f'Code does not use required phrase.',
                    code_problem=CodeProblem.StaticCheck,
                ))

        return issues
