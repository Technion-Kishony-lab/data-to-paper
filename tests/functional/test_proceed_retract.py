from typing import List, Dict

from scientistgtp.proceed_retract import ProceedRetract, FuncAndRetractions


class StepFailed(Exception):
    pass


class CounterProceedRetract(ProceedRetract):
    STATE_ATTRS: List[str] = ['data']

    def __init__(self,
                 run_plan: List[FuncAndRetractions] = None,
                 saved_states: List[Dict] = None,
                 current_step: int = -1,
                 data: List[int] = None,
                 should_fail: List[List[int]] = None):

        super().__init__(run_plan, saved_states, current_step)
        self.data = data
        self.should_fail = should_fail
        self.step_ran = []

    def _step_or_fail(self, step: int):
        self.data[step] += 1
        self.step_ran.append(step)
        if self.should_fail[len(self.step_ran) - 1]:
            raise StepFailed()

    def step0(self):
        self._step_or_fail(0)

    def step1(self):
        self._step_or_fail(1)

    def step2(self):
        self._step_or_fail(2)


RUN_PLAN: List[FuncAndRetractions] = [
    FuncAndRetractions('step0', StepFailed, [0, 0, ]),
    FuncAndRetractions('step1', StepFailed, [0, 1, ]),
    FuncAndRetractions('step2', StepFailed, [0, 2, ]),
]

expected_sequence = \
    [0, 0, 1, 2, 2, 0, 1, 1, 0, 1, 2]

should_fail = \
    [1, 0, 0, 1, 1, 0, 1, 1, 0, 0, 0]


def test_proceed_retract_run_correct_steps():
    runner = CounterProceedRetract(
        run_plan=RUN_PLAN,
        data=[0, 0, 0],
        should_fail=should_fail,
    )

    runner.run_all()

    assert runner.step_ran == expected_sequence
    assert runner.data == [1, 1, 1]

