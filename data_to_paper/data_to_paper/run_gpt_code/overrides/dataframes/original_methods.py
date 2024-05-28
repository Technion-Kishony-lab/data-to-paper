from pandas import DataFrame


def get_original_df_method(method_name):
    """
    Get the original DataFrame method.
    """
    method = getattr(DataFrame, method_name)
    while hasattr(method, 'wrapper_of'):
        method = method.wrapper_of
    return method