from .exceptions import CodeUsesForbiddenFunctions


def print(*args, **kwargs):
    raise CodeUsesForbiddenFunctions('print')
