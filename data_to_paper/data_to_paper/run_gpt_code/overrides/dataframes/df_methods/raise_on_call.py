from dataclasses import dataclass

from data_to_paper.run_gpt_code.run_issues import RunIssue, CodeProblem


@dataclass
class UnAllowedDataframeMethodCall(RunIssue):
    method_name: str = ''
    issue: str = "Your code uses the dataframe method `{method_name}`, which is not allowed."
    comment: str = 'Code uses forbidden method {method_name}'
    code_problem: CodeProblem = CodeProblem.RuntimeError


def raise_on_call(*args, original_method=None, on_change=None, **kwargs):
    raise UnAllowedDataframeMethodCall.from_current_tb(method_name=original_method.__name__)
