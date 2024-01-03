from __future__ import annotations
from typing import Optional, TYPE_CHECKING

from data_to_paper.run_gpt_code.run_issues import RunIssue, CodeProblem
from data_to_paper.run_gpt_code.user_script_name import is_called_from_user_script

if TYPE_CHECKING:
    from data_to_paper.run_gpt_code.overrides.scipy.override_scipy import ScipyPValueOverride


def is_namedtuple(obj):
    return isinstance(obj, tuple) and hasattr(obj, '_fields')


class NoIterTuple:
    def __init__(self, _tuple, created_by: Optional[str] = None, context: Optional[ScipyPValueOverride] = None,
                 should_raise: bool = True, should_register: bool = True):
        self._tuple = _tuple
        self.created_by = created_by
        self.context = context
        self.should_raise = should_raise
        self.should_register = should_register

    def __getattr__(self, item):
        return getattr(self._tuple, item)

    def __repr__(self):
        return repr(self._tuple)

    def __str__(self):
        return str(self._tuple)

    def __len__(self):
        return len(self._tuple)

    def _get_fields(self):
        try:
            return self._tuple._fields
        except AttributeError:
            return None

    def _raise_or_register_if_called_from_user_script(self, exception: RunIssue):
        if not is_called_from_user_script(offset=4):
            return
        if self.should_register and self.context:
            self.context.register_unpacking(self.created_by, self._get_fields())
        if self.should_raise:
            raise exception

    def __getitem__(self, item):
        if isinstance(item, int):
            self._raise_or_register_if_called_from_user_script(RunIssue.from_current_tb(
                code_problem=CodeProblem.NonBreakingRuntimeIssue,
                issue=f'Accessing the results of {self.created_by} by index can lead to coding mistakes.',
                instructions='Your code should instead explicitly access the attributes of the '
                             f'results: {", ".join(self._tuple._fields)}'
            ))
        return getattr(self._tuple, item)

    def __iter__(self):
        self._raise_or_register_if_called_from_user_script(RunIssue.from_current_tb(
            code_problem=CodeProblem.NonBreakingRuntimeIssue,
            issue=f'Unpacking, or otherwise iterating over, the results of {self.created_by} '
                  f'can lead to coding mistakes.',
            instructions='Your code should instead explicitly access the attributes of the '
                         f'results: {", ".join(self._tuple._fields)}'
        ))
        return iter(self._tuple)
