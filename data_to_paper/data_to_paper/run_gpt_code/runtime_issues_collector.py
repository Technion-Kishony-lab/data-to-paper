from __future__ import annotations

import os
from typing import List, Dict, Optional, Tuple, Iterable

from data_to_paper.run_gpt_code.types import RunIssue, CodeProblem
from data_to_paper.utils.types import ListBasedSet

RUNTIME_ISSUES_COLLECTORS: Dict[int, RunIssueCollector] = {}


def get_runtime_issue_collector() -> RunIssueCollector:
    process_id = os.getpid()
    if process_id not in RUNTIME_ISSUES_COLLECTORS:
        RUNTIME_ISSUES_COLLECTORS[process_id] = RunIssueCollector()
    return RUNTIME_ISSUES_COLLECTORS[process_id]


def create_and_add_issue(category: str, code_problem: CodeProblem, item: str, issue: str, instructions: str,
                         forgive_after: int = None):
    collector = get_runtime_issue_collector()
    collector.add_issue(
        RunIssue(category=category,
                 code_problem=code_problem,
                 item=item,
                 issue=issue,
                 instructions=instructions,
                 forgive_after=forgive_after)
    )


class RunIssueCollector:
    def __init__(self, issues: List[RunIssue] = None):
        if issues is None:
            issues = []
        self.issues: List[RunIssue] = issues

    def __enter__(self):
        self.issues = []
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return

    def add_issue(self, issue: RunIssue):
        self.issues.append(issue)

    def add_issues(self, issues: Iterable[RunIssue]):
        self.issues.extend(issues)

    def get_message_and_comment(self, most_severe_only: bool = True, end_with: str = '') -> Tuple[str, str]:
        """
        We compose all the issues into a single message, and a single comment.
        """
        issues = self._get_issues(most_severe_only)
        comments = ListBasedSet()

        s = ''
        if len(issues) > 1:
            s += 'There are some issues that need to be corrected:\n\n'

        code_problems = sorted(set(issue.code_problem for issue in issues))
        for code_problem in code_problems:
            categories = sorted(set(issue.category for issue in issues if issue.code_problem == code_problem))
            for category in categories:
                if category:
                    s += f'# {category}\n'
                issues_in_category = [issue for issue in issues if issue.category == category]
                unique_instructions = set(issue.instructions for issue in issues_in_category)
                for issue in issues_in_category:
                    if issue.item:
                        s += f'* {issue.item}:\n'
                    s += f'{issue.issue}\n'
                    if len(unique_instructions) > 1 and issue.instructions is not None:
                        s += f'{issue.instructions}\n'
                    s += '\n'
                    if issue.comment:
                        comments.add(issue.comment)
                if len(unique_instructions) == 1:
                    shared_instructions = unique_instructions.pop()
                    if shared_instructions:
                        s += f'{shared_instructions}\n'
        comment = '; '.join(comments)

        # Add the end_with message at the end:
        unique_end_with = set(issue.end_with for issue in issues)
        assert len(unique_end_with) == 1
        shared_end_with = unique_end_with.pop()
        if shared_end_with is not None:
            end_with = shared_end_with
        if end_with:
            s += f'\n{end_with}'
        return s, comment

    def get_most_severe_problem(self):
        return min(issue.code_problem for issue in self.issues)

    def _get_issues(self, most_severe_only: bool = True) -> List[RunIssue]:
        if most_severe_only:
            return [issue for issue in self.issues if issue.code_problem == self.get_most_severe_problem()]
        else:
            return self.issues

    def do_all_issues_request_small_change(self, highest_priority: bool = True) -> bool:
        return all(issue.requesting_small_change for issue in self._get_issues(highest_priority))
