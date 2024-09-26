import functools
import inspect
from dataclasses import dataclass
from typing import Iterable

from data_to_paper.run_gpt_code.base_run_contexts import MultiRunContext
from data_to_paper.run_gpt_code.attr_replacers import SystematicMethodReplacerContext, \
    PreventAssignmentToAttrs, AttrReplacer
from data_to_paper.run_gpt_code.run_issues import CodeProblem, RunIssue
from data_to_paper.text import dedent_triple_quote_str

from ..pvalue import convert_to_p_value, TrackPValueCreationFuncs


@dataclass
class SklearnFitOverride(SystematicMethodReplacerContext):

    def _get_all_modules(self) -> list:
        # add here all modules that have classes with fit methods:
        from sklearn import linear_model, svm
        return [linear_model, svm]

    def _should_replace(self, parent, attr_name, attr) -> bool:
        return attr_name.startswith('fit')

    def _get_custom_wrapper(self, parent, attr_name, original_func):

        @functools.wraps(original_func)
        def wrapped(obj, *args, **kwargs):
            result = original_func(obj, *args, **kwargs)
            if self._is_called_from_user_script():
                if hasattr(obj, '_prior_fit_results') and obj._prior_fit_results is result:
                    raise RunIssue.from_current_tb(
                        category='Sklearn: good practices',
                        issue=f"The `{original_func.__name__}` function was already called on this object. ",
                        instructions=f"Multiple calls should be avoided as the same result instance is returned again.",
                        code_problem=CodeProblem.RuntimeError,
                    )
                obj._prior_fit_results = result

            return result

        return wrapped


def _f_regression(*args, original_func=None, **kwargs):
    p = original_func(*args, **kwargs)
    return (p[0], convert_to_p_value(p[1], created_by='f_regression'))


@dataclass
class SklearnPValue(AttrReplacer, TrackPValueCreationFuncs):
    """
    f_regression should return array of PValue objects instead of floats.
    """
    obj_import_str: str = 'sklearn.feature_selection'
    attr: str = 'f_regression'
    wrapper: callable = _f_regression
    send_original_to_wrapper: bool = True


@dataclass
class SklearnSearchLimitCheck(SystematicMethodReplacerContext):
    max_iterations: int = 12  # Default max iterations limit

    def _get_all_parents(self) -> list:
        # add here all modules that have classes with fit methods:
        from sklearn.model_selection import ParameterGrid, ParameterSampler
        return [ParameterGrid, ParameterSampler]

    def _should_replace(self, parent, attr_name, attr) -> bool:
        return attr_name == "__len__"

    def _get_estimator_class_name(self):
        # Inspect the stack and find the class name of the estimator
        for frame_record in inspect.stack():
            if 'self' in frame_record.frame.f_locals:
                instance = frame_record.frame.f_locals['self']
                if hasattr(instance, 'fit'):
                    return instance.estimator.__class__.__name__
        return 'Unknown'

    def _get_custom_wrapper(self, parent, attr_name, original_func):

        @functools.wraps(original_func)
        def wrapped(obj, *args, **kwargs):
            original_len = original_func(obj, *args, **kwargs)
            if original_len > self.max_iterations:
                estimator_class_name = self._get_estimator_class_name()
                raise RunIssue.from_current_tb(
                    category='Sklearn: too many iterations',
                    issue=dedent_triple_quote_str(f"""
                        The presumed total number of training iterations ({original_len}) for the estimator \t
                        {estimator_class_name} exceeds the maximum allowed iterations ({self.max_iterations}).
                        Notice that the amount of iterations is a multiplication of the numbers of possible values \t
                        for each parameter when using GridSearchCV or n_iter when using RandomizedSearchCV.
                        """),
                    instructions=f"use only a subset of the parameters or reduce the number of iterations.",
                    code_problem=CodeProblem.RuntimeError)
            return original_len

        return wrapped


@dataclass
class SklearnRandomStateOverride(SystematicMethodReplacerContext):
    """
    This class overrides any provided sklearn class constructor (__init__) that supports random_state
    from sklearn to set random_state=0, ensuring reproducibility.
    """
    def _get_all_parents(self) -> list:
        # Add here all classes that have a random_state parameter in their constructor:
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.linear_model import ElasticNet
        from sklearn.neural_network import MLPRegressor
        return [RandomForestRegressor, ElasticNet, MLPRegressor]

    def _should_replace(self, parent, attr_name, attr) -> bool:
        if not attr_name == '__init__':
            return False
        sig = inspect.signature(attr)
        assert 'random_state' in sig.parameters, f"Expected random_state to be in the signature of {parent.__name__}"
        return True

    def _get_custom_wrapper(self, parent, attr_name, original_func):

        @functools.wraps(original_func)
        def wrapped(obj, *args, **kwargs):
            # Set random_state=0 if not explicitly passed
            if 'random_state' not in kwargs:
                kwargs['random_state'] = 0

            # Call the original constructor
            return original_func(obj, *args, **kwargs)

        return wrapped


@dataclass
class SklearnSingleNNSizeOverride(PreventAssignmentToAttrs):
    """
    This class overrides MLPRegressor and MLPClassifier to raise warning if the hidden_layer_sizes is too large.
    """
    obj_import_str: str = None  # 'sklearn.neural_network.MLPRegressor', 'sklearn.neural_network.MLPClassifier'
    forbidden_set_attrs: Iterable[str] = ('hidden_layer_sizes', )
    max_layers: int = 2
    max_neurons_per_layer: int = 50

    def _is_called_from_user_script(self) -> bool:
        return True

    def _raise_exception(self, attr, value):
        # if value is the same as default, do not raise exception - get value using inspect and compare
        if value == inspect.signature(self.obj).parameters[attr].default:
            return
        # Check depth:
        instructions = f"Please use a smaller hidden_layer_sizes of up to {self.max_layers} layers with " \
                       f"maximum of {self.max_neurons_per_layer} neurons per layer."
        if len(value) > self.max_layers:
            raise RunIssue.from_current_tb(
                category='Too many layers',
                issue=f"The hidden_layer_sizes ({len(value)}) is too large!\n",
                instructions=instructions,
                code_problem=CodeProblem.RuntimeError)
        # Check width:
        for layer, layer_size in enumerate(value):
            if layer_size > self.max_neurons_per_layer:
                raise RunIssue.from_current_tb(
                    category='Too large hidden layer',
                    issue=f"The hidden_layer_sizes, has a layer ({layer}) with too many neurons ({layer_size})!\n",
                    instructions=instructions,
                    code_problem=CodeProblem.RuntimeError)


@dataclass
class SklearnNNSizeOverride(MultiRunContext):
    contexts: Iterable[SklearnSingleNNSizeOverride] = (
        SklearnSingleNNSizeOverride(obj_import_str='sklearn.neural_network.MLPRegressor'),
        SklearnSingleNNSizeOverride(obj_import_str='sklearn.neural_network.MLPClassifier'),
    )
