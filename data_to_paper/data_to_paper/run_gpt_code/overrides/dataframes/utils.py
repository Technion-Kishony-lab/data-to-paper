
def format_float(value: float, float_format: str = '.4g') -> str:
    if value.is_integer():
        return str(int(value))
    else:
        return f'{value:{float_format}}'
