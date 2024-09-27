from data_to_paper.text.text_formatting import short_repr


def get_func_call_str(func_name: str, args, kwargs):
    return func_name + '(' + ', '.join(
        [short_repr(arg) for arg in args] + [f'{k}={short_repr(v)}' for k, v in kwargs.items()]) + ')'
