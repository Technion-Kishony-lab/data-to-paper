from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class RuntimeIssue:
    category: str
    order: int
    item: str
    issue: str
    instructions: str
    forgive_after: int = None  # Forgive after this many times,  None means never forgive


RUNTIME_ISSUES_COLLECTORS: Dict[int, RuntimeIssueCollector] = {}


def get_runtime_issue_collector() -> RuntimeIssueCollector:
    process_id = os.getpid()
    if process_id not in RUNTIME_ISSUES_COLLECTORS:
        RUNTIME_ISSUES_COLLECTORS[process_id] = RuntimeIssueCollector()
    return RUNTIME_ISSUES_COLLECTORS[process_id]


def create_and_add_issue(category: str, order: int, item: str, issue: str, instructions: str,
                         forgive_after: int = None):
    collector = get_runtime_issue_collector()
    collector.add_issue(RuntimeIssue(category, order, item, issue, instructions, forgive_after))


class RuntimeIssueCollector:
    def __init__(self):
        self.issues: List[RuntimeIssue] = []

    def __enter__(self):
        self.issues = []
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return

    def add_issue(self, issue: RuntimeIssue):
        self.issues.append(issue)

    def get_message(self) -> Optional[str]:
        if not self.issues:
            return None
        orders_to_categories = {}
        for issue in self.issues:
            orders_to_categories.setdefault(issue.order, set()).add(issue.category)

        s = 'There are some issues that need to be corrected:\n\n'
        order, categories = next(iter(orders_to_categories.items()))
        for category in categories:
            s += f'# {category}\n'
            issues_in_category = [issue for issue in self.issues if issue.category == category]
            for issue in issues_in_category:
                s += f'* {issue.item}:\n'
                s += f'{issue.issue}\n'
            s += f'\n{issue.instructions}\n'
        return s
