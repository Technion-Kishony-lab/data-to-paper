from data_to_paper.env import NUM_DIGITS_FOR_FLOATS


def format_float(value: float, float_format: str = None) -> str:
    float_format = float_format or f'.{NUM_DIGITS_FOR_FLOATS}g'

    if value.is_integer():
        return str(int(value))
    else:
        return f'{value:{float_format}}'
