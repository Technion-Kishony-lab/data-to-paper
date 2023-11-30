import builtins
import json
import openai


def _serialize_exception(exception):
    return {
        'is_exception': True,
        'type': type(exception).__name__,
        'args': exception.args,
    }


def _serialize_item(item):
    if isinstance(item, Exception):
        item = _serialize_exception(item)
    return item


def _de_serialize_item(item):
    if isinstance(item, dict) and 'is_exception' in item and item['is_exception'] is True:
        exception_type = item['type']
        args = tuple(item['args'])
        # if exception in builtins:
        if hasattr(builtins, exception_type):
            exception = getattr(builtins, exception_type)(*args)
        elif hasattr(openai.error, exception_type):
            if exception_type == 'InvalidRequestError':
                exception = getattr(openai.error, exception_type)(*args, param=None)
            else:
                exception = getattr(openai.error, exception_type)(*args)
        else:
            exception = Exception(*args)
        return exception
    else:
        return item


def _dump_to_json(serialized_data, filename):
    with open(filename, 'w') as file:
        json.dump(serialized_data, file, indent=4, sort_keys=True)


def _load_from_json(filename):
    with open(filename, 'r') as file:
        return json.load(file)


def save_list_to_json(data: list, filename):
    serialized_data = [_serialize_item(item) for item in data]
    _dump_to_json(serialized_data, filename)


def load_list_from_json(filename):
    serialized_data = _load_from_json(filename)
    return [_de_serialize_item(item) for item in serialized_data]
