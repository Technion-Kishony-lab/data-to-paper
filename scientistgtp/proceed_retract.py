import copy
from typing import List, NamedTuple, Dict, Type

from .exceptions import FailedRunningStep


class FuncAndRetractions(NamedTuple):
    """
    Indicates a function to run and number of steps to go back upon consecutive failures.
    """

    func_name: str
    """
    Name of method to run
    """

    exception: Type[Exception]
    """
    Expected exception upon failure
    """

    retractions_on_failure: List[int]
    """
    A list containing the number of backward steps to retract upon consecutive failures of the function.
    Value of 0 indicates re-running the same step, value 1 indicates going one step backwards, etc.
    """


RunPlan = List[FuncAndRetractions]


class ProceedRetract:
    """
    Allows running analysis steps that sequentially manipulate the object state.
    The methods ran in sequence may be impure functions and may also raise exceptions. When exceptions are raised,
    we follow a retraction plan which specifies how many steps to go back certain number of steps.

             proceed          proceed          proceed
    state[0] >>>>>>> state[1] >>>>>>> state[2] >>>>>>> state[3] ...
             func[0]          func[1]          func[2]
                        ^                                 v
                        ^                                 v
                        <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
                       retract 2 steps upon failure of func[2]

    STATE_ATTRS:  list of all the attributes that define the data manipulated by the funcs.
    run_plan:     list of FuncAndRetractions, specifying the order of the functions to run and how many steps backwards
                  to retract to upon failure.
    saved_state:  list of dicts containing the state at each successful step.
    current_step: -1 - uninitiated. 0 - after copying the initial step to saved_step. 1 - after running step 0.
    """

    STATE_ATTRS: List[str] = []

    def __init__(self,
                 run_plan: RunPlan = None,
                 saved_states: List[Dict] = None,
                 current_step: int = -1):
        self.run_plan = run_plan or []
        self.saved_states = saved_states or []
        self.current_step = current_step
        self.num_failures = [0] * self.num_steps  # the number of time each step failed since last success.

    @property
    def num_steps(self):
        return len(self.run_plan)

    def initialize(self):
        self.saved_states = []
        self.current_step = 0
        self.save_current_state()

    def get_copy_of_current_state(self):
        return {attr: copy.deepcopy(getattr(self, attr)) for attr in self.STATE_ATTRS}

    def save_current_state(self):
        assert len(self.saved_states) == self.current_step
        self.saved_states.append(self.get_copy_of_current_state())

    def go_to_step(self, step: int):
        self.saved_states = self.saved_states[: step + 1]
        last_state = self.saved_states[-1]
        for attr, value in last_state.items():
            setattr(self, attr, copy.deepcopy(value))
        self.current_step = step

    def run_all(self):
        while self.current_step < self.num_steps:
            self.run_next_step()

    def run_next_step(self):
        step = self.current_step
        if step == -1:
            self.initialize()
            return

        func_and_retractions = self.run_plan[step]
        try:
            func = getattr(self, func_and_retractions.func_name)
            func()
        except func_and_retractions.exception:
            num_backward_steps = func_and_retractions.retractions_on_failure[self.num_failures[step]]
            self.go_to_step(step - num_backward_steps)
            self.num_failures[step] += 1
            if self.num_failures[step] > len(func_and_retractions.retractions_on_failure):
                raise FailedRunningStep(step=step, func=func_and_retractions.func_name)
        except Exception:
            raise
        else:
            self.num_failures[step] = 0
            self.current_step += 1
            self.save_current_state()
