import copy
from typing import List, NamedTuple, Dict, Type, Union, Tuple, Any

from .exceptions import FailedRunningStep
import colorama


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
    execution_plan:
                  list of FuncAndRetractions, specifying the order of the functions to run and how many steps backwards
                  to retract to upon failure.
    saved_state:  list of dicts containing the state at each successful step.
    current_step: -1 - uninitiated. 0 - after copying the initial step to saved_step. 1 - after running step 0.
    """

    STATE_ATTRS: List[str] = []

    def __init__(self, execution_plan: RunPlan = None):
        self.saved_states_by_name: Dict[str: State] = {}
        self.execution_plan = execution_plan or []
        self.saved_states_by_step: List[State] = []
        self.current_step: int = -1
        self.num_failures: List[int] = [0] * self.num_steps  # the number of time each step failed since last success.

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
            self.run_next_step(annotate)

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
                print(colorama.Fore.RED + f'Running {func_and_retractions.func_name} ...' + colorama.Style.RESET_ALL)
            func()
        except func_and_retractions.exception as e:
            num_backward_steps = func_and_retractions.retractions_on_failure[self.num_failures[step]]
            if annotate:
                print(e)
                if num_backward_steps == 0:
                    print('Retrying.')
                elif num_backward_steps == 1:
                    print('Retracting one step backwards.')
                else:
                    print(f'Retracting {num_backward_steps} steps backwards.')
                print()
            self.reset_state_to(step - num_backward_steps)
            self.num_failures[step] += 1
            if self.num_failures[step] > len(func_and_retractions.retractions_on_failure):
                raise FailedRunningStep(step=step, func_name=func_and_retractions.func_name)
        except Exception:
            raise
        else:
            # Step was successful
            self.num_failures[step] = 0
            self.current_step += 1
            self.save_current_state_by_step()
