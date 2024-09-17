import builtins
import openai


def serialize_exception(exception: Exception):
    return {
        'is_exception': True,
        'type': type(exception).__name__,
        'args': exception.args,
    }


def is_exception(item):
    return isinstance(item, dict) and 'is_exception' in item and item['is_exception'] is True


def de_serialize_exception(item) -> Exception:
    assert is_exception(item)
    exception_type = item['type']
    args = tuple(item['args'])
    if hasattr(builtins, exception_type):
        # if exception in builtins:
        exception = getattr(builtins, exception_type)(*args)
    elif hasattr(openai.error, exception_type):
        if exception_type == 'InvalidRequestError':
            exception = getattr(openai.error, exception_type)(*args, param=None)
        else:
            exception = getattr(openai.error, exception_type)(*args)
    else:
        exception = Exception(*args)
    return exception
