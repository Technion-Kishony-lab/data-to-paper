import copy
from typing import List, NamedTuple, Dict, Type, Union, Tuple, Any, Optional, Callable

from scientistgpt.exceptions import FailedRunningStep
from scientistgpt.utils.text_utils import print_red


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
    Value of 0 indicates re-running the same step, value 1 indicates going one step backwards, etc.
    """


RunPlan = List[FuncAndRetractions]

State = Dict[str, Any]


class ProceedRetract:
    """
    Allows running analysis steps that sequentially manipulate the object state.
    The steps to run may be impure functions (results change with repeated calls, like when we approach chatgpt).
    These steps may also fail, raise exceptions (for example, when we try to run a code produced by chatgpt).

    STATE_ATTRS:    list of all the attributes that define the data manipulated by the functions that we intend to run.
                    This list is used by ProceedRetract to save the instance state at different steps to be able to
                    retrieve and go back upon downstream failures.

    saved_states_by_step:
                    list of dicts containing the state at each successful step.

    saved_states_by_name:
                    dict of str:dict containing prior states saved by name.

    execution_plan: a list of FuncAndRetractions specifying the order of methods to run, which exception types to
                    expect from each method, and what to do upon exception. In particular, the retractions_on_failure
                    attribute of each FuncAndRetractions specifies how many steps to go back upon consecutive failures.

    current_step:   indicates where we are in the execution plan.
                    -1 - uninitiated. 0 - after copying the initial step to saved_step. 1 - after running step 0.


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

    STATE_ATTRS: List[str] = []

    def __init__(self, execution_plan: RunPlan = None, callback: Optional[Callable] = None):
        self.saved_states_by_name: Dict[str: State] = {}
        self.execution_plan = execution_plan or []
        self.saved_states_by_step: List[State] = []
        self.current_step: int = -1
        self._num_failures: List[int] = [0] * self.num_steps  # the number of time each step failed since last success.
        self.callback = callback

    @property
    def num_steps(self):
        return len(self.execution_plan)

    def initialize(self):
        self.saved_states_by_step = []
        self.current_step = 0
        self.save_current_state_by_step()

    def get_copy_of_current_state(self):
        return {attr: copy.deepcopy(getattr(self, attr)) for attr in self.STATE_ATTRS}

    def save_current_state_by_step(self):
        assert len(self.saved_states_by_step) == self.current_step
        self.saved_states_by_step.append(self.get_copy_of_current_state())

    def save_current_state_by_name(self, name):
        self.saved_states_by_name[name] = self.get_copy_of_current_state()

    def reset_state_to(self, step_or_name: Union[int, str]):
        """
        Reset to a saved state.

        step_or_name: can be an int for steps saved sequentially, or a str for states saved by name.
        """
        if isinstance(step_or_name, int):
            self.saved_states_by_step = self.saved_states_by_step[: step_or_name + 1]
            new_state = self.saved_states_by_step[step_or_name]
            self.current_step = step_or_name
        else:
            new_state = self.saved_states_by_name[step_or_name]

        for attr, value in new_state.items():
            setattr(self, attr, copy.deepcopy(value))

    def run_all(self, annotate: bool = False):
        while self.current_step < self.num_steps:
            try:
                self.run_next_step(annotate)
                step_status = "success"
            except Exception as e:
                step_status = str(e)

            if self.callback:
                self.callback(self, step_status)

    def run_next_step(self, annotate: bool = False):
        """
        Run the next step in the execution plan.

        If step fails, repeat or go back based on the retractions_on_failure of the executed step in the
        execution_plan.

        :param annotate: whether to print text messages indicating progress and retractions
        """
        step = self.current_step
        if step == -1:
            self.initialize()
            return

        func_and_retractions = self.execution_plan[step]
        try:
            func = getattr(self, func_and_retractions.func_name)
            if annotate:
                print_red(f'Running {func_and_retractions.func_name} ...')
            func()
        except func_and_retractions.exception as e:
            num_backward_steps = func_and_retractions.retractions_on_failure[self._num_failures[step]]
            if annotate:
                print(e)
                if num_backward_steps == 0:
                    print_red('ProceedRetract: Retrying failed step.')
                elif num_backward_steps == 1:
                    print_red('ProceedRetract: Retracting one step backwards.')
                else:
                    print_red(f'ProceedRetract: Retracting {num_backward_steps} steps backwards.')
                print()
            self.reset_state_to(step - num_backward_steps)
            self._num_failures[step] += 1
            if self._num_failures[step] > len(func_and_retractions.retractions_on_failure):
                raise FailedRunningStep(step=step, func_name=func_and_retractions.func_name)
        except Exception:
            raise
        else:
            # Step was successful
            self._num_failures[step] = 0
            self.current_step += 1
            self.save_current_state_by_step()
