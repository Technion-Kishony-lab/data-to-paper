import functools
import inspect
from dataclasses import dataclass

from data_to_paper.run_gpt_code.overrides.attr_replacers import SystematicMethodReplacerContext


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
            if self._is_called_from_data_to_paper():
                if hasattr(obj, '_prior_fit_results') and obj._prior_fit_results is result:
                    raise RuntimeWarning(
                        f"The `{original_func.__name__}` function was already called on this object. "
                        f"Multiple calls should be avoided as the same result instance is returned again.")
                obj._prior_fit_results = result

            return result

        return wrapped


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
                raise RuntimeWarning(f"The presumed total number of training iterations ({original_len}) for "
                                     f"{estimator_class_name} exceeds the maximum allowed iterations "
                                     f"({self.max_iterations}). \nNotice that the amount of iterations is a "
                                     f"multiplication of the numbers of possible values for each parameter when using "
                                     f"GridSearchCV or n_iter when using RandomizedSearchCV. \n"
                                     f"use only a subset of the parameters or reduce the number of iterations.")
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
class SklearnNNSizeOverride(SystematicMethodReplacerContext):
    """
    This class overrides MLPRegressor and MLPClassifier to raise warning if the hidden_layer_sizes is too large.
    """
    max_layers: int = 2
    max_neurons_per_layer: int = 50

    def _get_all_parents(self) -> list:
        from sklearn.neural_network import MLPRegressor
        from sklearn.neural_network import MLPClassifier
        return [MLPRegressor, MLPClassifier]

    def _should_replace(self, parent, attr_name, attr) -> bool:
        sig = inspect.signature(attr)
        assert 'hidden_layer_sizes' in sig.parameters, \
            f"Expected hidden_layer_sizes to be in the signature of {parent.__name__}"
        return attr_name == '__init__'

    def _get_custom_wrapper(self, parent, attr_name, original_func):

        @functools.wraps(original_func)
        def wrapped(obj, *args, **kwargs):

            sig = inspect.signature(original_func)
            # apply default and get the hidden_layer_sizes:
            bound_args = sig.bind(obj, *args, **kwargs)
            bound_args.apply_defaults()

            # Check depth:
            hidden_layer_sizes = bound_args.arguments['hidden_layer_sizes']
            if len(hidden_layer_sizes) > self.max_layers:
                raise RuntimeWarning(f"The given hidden_layer_sizes ({len(hidden_layer_sizes)}) is too large!\n"
                                     f"We only allow up to {self.max_layers} layers with {self.max_neurons_per_layer} "
                                     f"max neurons per layer.")

            # Check width:
            for layer, layer_size in enumerate(hidden_layer_sizes):
                if layer_size > self.max_neurons_per_layer:
                    raise RuntimeWarning(f"The given hidden_layer_sizes, has a layer ({layer}) with too many neurons!\n"
                                         f"We only allow up to {self.max_layers} layers with "
                                         f"{self.max_neurons_per_layer} max neurons per layer.")

            # Call the original constructor
            return original_func(obj, *args, **kwargs)

        return wrapped
