from dataclasses import dataclass
from typing import List, NamedTuple, Type, Union, Tuple, Optional, Callable

from scientistgpt.exceptions import FailedRunningStep
from scientistgpt.utils.text_utils import print_magenta


class FuncAndRetractions(NamedTuple):
    """
    Indicates a function to run and number of steps to go back upon consecutive failures.
    """

    func_name: str
    """
    Name of method to run.
    """

    exception: Union[Type[Exception], Tuple[Type[Exception], ...]]
    """
    Expected exception(s) upon failure.
    """

    retractions_on_failure: List[int]
    """
    A list containing the number of backward steps to retract upon consecutive failures of the function.
    Value of 0 indicates re-running the same step; 
    Value of 1 indicates going one step backwards, etc.
    """


ExecutionPlan = List[FuncAndRetractions]


@dataclass
class ProceedRetract:
    """
    Run analysis steps sequentially and retract to earlier steps upon downstream failures.

    The steps to run may be impure functions (results can change with repeated calls, e.g. when we approach chatgpt).
    Steps may also fail, raise exceptions (for example, when we try to run a code produced by chatgpt).

    execution_plan: a list of FuncAndRetractions specifying the order of methods to run, which exception types to
                    expect from each method upon failure, and what to do when such failures occur. In particular,
                    the retractions_on_failure attribute of each FuncAndRetractions specifies how many steps to go back
                    upon consecutive failures. The class keeps track of the number of consecutive failures for each
                    step (this number resets upon successful completion of a step).

    current_step:   indicates where we are in the execution plan. 0 - before the first step.


    Here is an example of an execution plan:
    [
        FuncAndRetractions('func0', (), []),
        FuncAndRetractions('func1', (), []),
        FuncAndRetractions('func2', (), [1, 2]),  # go back one step on 1st failure and 2 steps on the second failure.
    ]

             proceed          proceed          proceed
    state[0] >>>>>>> state[1] >>>>>>> state[2] >>>>>>> state[3] ...
              func0            func1            func2
                        ^                ^                v
                        ^                ^                v
                        ^                ^<<<<<<<<<<<<<<<<+
                        ^                    1st failure  v
                        ^                                 v
                        <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
                                    2nd failure

    """

    execution_plan: ExecutionPlan = None
    print_level: int = 1  # 0 - no printing, 1 - print retractions, 2 - print all

    def __post_init__(self):
        self.current_step: int = 0

        # Number of times each step has failed since the last time it succeeded:
        self._num_failures: List[int] = [0] * self.num_steps

        # Total number of times each step has been tried
        self._num_tries: List[int] = [0] * self.num_steps

    def print_comment(self, comment: str, action: str):
        if action == 'proceed' and self.print_level >= 2 or action == 'retract' and self.print_level >= 1:
            print_magenta(comment)

    @property
    def num_steps(self):
        return len(self.execution_plan)

    def run_all(self):
        while self.current_step < self.num_steps:
            self.run_next_step()

    def get_total_number_of_tries_for_current_step(self) -> int:
        return self._num_tries[self.current_step]

    def get_number_of_successive_failures_for_current_step(self) -> int:
        return self._num_failures[self.current_step]

    def get_allowed_number_of_successive_failures_for_current_step(self) -> int:
        return len(self.execution_plan[self.current_step].retractions_on_failure)


    def run_next_step(self):
        """
        Run the next step in the execution plan.

        If step fails, repeat or go back based on the retractions_on_failure of the executed step in the
        execution_plan.
        """
        step = self.current_step

        func_and_retractions = self.execution_plan[step]
        try:
            func = getattr(self, func_and_retractions.func_name)
            self.print_comment(f'Running {func_and_retractions.func_name} ...', 'proceed')
            self._num_tries[step] += 1
            func()
        except func_and_retractions.exception as e:
            num_backward_steps = func_and_retractions.retractions_on_failure[self._num_failures[step]]
            self.print_comment(str(e) + '\n' + self._retraction_comment(num_backward_steps), 'retract')
            self.current_step = step - num_backward_steps
            self._num_failures[step] += 1
            if self._num_failures[step] > len(func_and_retractions.retractions_on_failure):
                raise FailedRunningStep(step=step, func_name=func_and_retractions.func_name)
        except Exception:
            raise
        else:
            # Step was successful
            self._num_failures[step] = 0
            self.current_step += 1

    @staticmethod
    def _retraction_comment(num_steps):
        if num_steps == 0:
            return 'ProceedRetract: Retrying failed step.'
        elif num_steps == 1:
            return 'ProceedRetract: Retracting one step backwards.'
        else:
            return f'ProceedRetract: Retracting {num_steps} steps backwards.'
