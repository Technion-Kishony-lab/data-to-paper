from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List, Tuple

from data_to_paper.run_gpt_code.exceptions import FailedRunningCode
from data_to_paper.text import word_count
from data_to_paper.utils.replacer import format_value
from data_to_paper.utils.types import IndexOrderedEnum, ListBasedSet

MAX_WORDS_BEFORE_TERMINATING_ISSUE_LIST = 150


class CodeProblem(IndexOrderedEnum):
    """
    Code problems are sorted by severity, in the sense of progressively closer to a final fully working code.
    """
    NoCode = 'No code'
    IncompleteBlock = 'Incomplete block'
    NotSingleBlock = 'Not single block'
    StaticCheck = 'Static check'
    TimeoutError = 'Timeout error'
    RuntimeError = 'Runtime error'
    SyntaxError = 'Syntax error'
    MissingOutputFiles = 'Missing output files'
    NonBreakingRuntimeIssue = 'Non-breaking runtime issue'
    OutputFileCallingSyntax = 'Problem in the calling syntax of the output creation func'
    OutputFileContentA = 'Output file content first check (analysis stage)'
    OutputFileContinuity = 'Check dependency on previous output'
    OutputFileContentB = 'Output file content second check (displayitems stage)'
    OutputFileCompilation = 'Output file failed compilation'
    OutputFileAnnotation = 'Output file annotation'
    AllOK = 'All OK'

    def is_incomplete(self) -> bool:
        return self <= CodeProblem.IncompleteBlock

    def is_not_single_block(self) -> bool:
        return self == CodeProblem.NotSingleBlock

    def is_static_check(self) -> bool:
        return self == CodeProblem.StaticCheck

    def is_run_failed(self) -> bool:
        return CodeProblem.TimeoutError <= self <= CodeProblem.SyntaxError

    def is_missing_output_files(self) -> bool:
        return self == CodeProblem.MissingOutputFiles

    def is_run_completed_and_files_created(self) -> bool:
        return self >= CodeProblem.NonBreakingRuntimeIssue

    def get_stage(self) -> int:
        if self.is_incomplete():
            return 0
        elif self.is_not_single_block():
            return 1
        elif self.is_static_check():
            return 2
        elif self.is_run_failed():
            return 3
        elif self.is_missing_output_files():
            return 4
        elif self.is_run_completed_and_files_created():
            return 5
        else:
            raise NotImplementedError(f'Unknown problem stage for {self}')


@dataclass
class RunIssue(FailedRunningCode):
    code_problem: CodeProblem = None
    category: str = ''
    item: str = ''
    issue: str = ''
    instructions: str = ''
    comment: str = None
    end_with: Optional[str] = None
    requesting_small_change: bool = False
    forgive_after: Optional[int] = None  # Forgive after this many times,  None means never forgive

    @classmethod
    def from_current_tb(cls, code_problem: CodeProblem = None, category: str = None, item: str = None,
                        issue: str = None, instructions: str = None, comment: str = None,
                        end_with: Optional[str] = None,
                        requesting_small_change: bool = False, forgive_after: int = None, **kwargs):
        explicit_kwargs = {'code_problem': code_problem, 'category': category, 'item': item, 'issue': issue,
                           'instructions': instructions, 'comment': comment, 'end_with': end_with,
                           'requesting_small_change': requesting_small_change, 'forgive_after': forgive_after
                           }
        kwargs = kwargs | {k: v for k, v in explicit_kwargs.items() if v is not None}
        return super().from_current_tb(**kwargs)

    def formatted(self) -> RunIssue:
        return RunIssue(
            tb=self.tb,
            code_problem=self.code_problem,
            category=format_value(self, self.category),
            item=format_value(self, self.item),
            issue=format_value(self, self.issue),
            instructions=format_value(self, self.instructions),
            comment=format_value(self, self.comment),
            end_with=format_value(self, self.end_with),
            requesting_small_change=self.requesting_small_change,
            forgive_after=self.forgive_after,
        )

    def __str__(self):
        return RunIssues([self]).get_message_and_comment()[0]

    def __hash__(self):
        return hash((self.code_problem, self.category, self.item, self.issue, self.instructions, self.end_with))


class RunIssues(List[RunIssue]):

    def append_if_does_not_exist(self, issue: RunIssue):
        if issue not in self:
            self.append(issue)

    def get_message_and_comment(self, most_severe_only: bool = True, end_with: str = ''
                                ) -> Tuple[str, str, List[RunIssue]]:
        """
        We compose all the issues into a single message, and a single comment.
        """
        issues = [issue.formatted() for issue in self._get_issues(most_severe_only)]
        comments = ListBasedSet()

        if not issues:
            return 'All OK', '', []

        s = ''
        if len(issues) > 1:
            s += 'There are some issues that need to be corrected:\n\n'

        code_problems = sorted(set(issue.code_problem for issue in issues))
        posted_issues = []
        for code_problem in code_problems:
            categories = sorted(set(issue.category for issue in issues if issue.code_problem == code_problem))
            notes = []
            for category in categories:
                note = ''
                if category:
                    note += f'# {category}\n'
                issues_in_category = [issue for issue in issues if issue.category == category]
                unique_instructions = set(issue.instructions for issue in issues_in_category)
                shared_instructions = unique_instructions.pop() if len(unique_instructions) == 1 else None
                shared_instructions_word_count = word_count(shared_instructions) if shared_instructions else 0
                last_linenos_and_lines = None
                last_item = None
                for issue in issues_in_category:
                    posted_issues.append(issue)
                    if issue.item and issue.item != last_item:
                        last_item = issue.item
                        note += f'## {issue.item}:\n'
                    if issue.linenos_and_lines and issue.linenos_and_lines != last_linenos_and_lines:
                        last_linenos_and_lines = issue.linenos_and_lines
                        note += 'On line:\n'
                        note += '\n'.join(f'{lineno}: {line}' for lineno, line in issue.linenos_and_lines)
                        note += '\n'
                    note += f'{issue.issue.strip()}\n'
                    if shared_instructions is None and issue.instructions is not None:
                        note += f'{issue.instructions.strip()}\n'
                    note += '\n'
                    if issue.comment:
                        comments.add(issue.comment)
                    if word_count(note) + shared_instructions_word_count > MAX_WORDS_BEFORE_TERMINATING_ISSUE_LIST:
                        break
                if shared_instructions:
                    note += f'{shared_instructions}\n'
                notes.append(note)
            s += '\n\n'.join(notes)
        comment = '; '.join(comments)

        # Add the end_with message at the end:
        unique_end_with = set(issue.end_with for issue in issues)
        assert len(unique_end_with) == 1
        shared_end_with = unique_end_with.pop()
        if shared_end_with is not None:
            end_with = shared_end_with
        if end_with:
            s += f'\n{end_with}'
        return s, comment, posted_issues

    def get_most_severe_problem(self):
        return min(issue.code_problem for issue in self)

    def _get_issues(self, most_severe_only: bool = True) -> List[RunIssue]:
        if most_severe_only:
            return [issue for issue in self if issue.code_problem == self.get_most_severe_problem()]
        else:
            return list(self)

    def do_all_issues_request_small_change(self, highest_priority: bool = True) -> bool:
        return all(issue.requesting_small_change for issue in self._get_issues(highest_priority))
