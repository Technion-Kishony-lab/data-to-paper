import inspect

from data_to_paper.run_gpt_code.overrides.attr_replacers import AttrReplacer


def init_wrapper_with_random_state(*args, original_func=None, **kwargs):
    """
    Wrapper function for sklearn class constructors (__init__). 
    It sets random_state to 0 if the class constructor supports it and if it's not provided.
    """
    # Check if 'random_state' is a parameter in the original function and not provided by the user
    params = inspect.signature(original_func).parameters
    if 'random_state' in params and 'random_state' not in kwargs:
        kwargs['random_state'] = 0

    # Call the original constructor
    return original_func(*args, **kwargs)

def sklearn_rf_random_state_init_replacer():
    return AttrReplacer(obj_import_str='sklearn.ensemble.RandomForestRegressor', attr='__init__',
                        wrapper=init_wrapper_with_random_state, send_original_to_wrapper=True)

def sklearn_nn_random_state_init_replacer():
    return AttrReplacer(obj_import_str='sklearn.neural_network.MLPRegressor', attr='__init__',
                        wrapper=init_wrapper_with_random_state, send_original_to_wrapper=True)

def sklearn_en_random_state_init_replacer():
    return AttrReplacer(obj_import_str='sklearn.linear_model.ElasticNet', attr='__init__',
                        wrapper=init_wrapper_with_random_state, send_original_to_wrapper=True)

def sklearn_random_state_init_replacer():
    return [sklearn_rf_random_state_init_replacer(), sklearn_nn_random_state_init_replacer(),
            sklearn_en_random_state_init_replacer()]
