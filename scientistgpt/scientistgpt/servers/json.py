import builtins
import json


def save_to_json(data: list, filename):
    serialized_data = []
    for item in data:
        if isinstance(item, Exception):
            item = {
                'is_exception': True,
                'type': type(item).__name__,
                'message': str(item),
                'args': item.args,
            }
        serialized_data.append(item)

    with open(filename, 'w') as file:
        json.dump(serialized_data, file, indent=4, sort_keys=True)


def load_from_json(filename):
    with open(filename, 'r') as file:
        serialized_data = json.load(file)

    data = []
    for item in serialized_data:
        if isinstance(item, dict) and 'is_exception' in item and item['is_exception'] is True:
            exception_type = item['type']
            message = item['message']
            args = (message,) + tuple(item['args'])
            # if exception in builtins:
            if hasattr(builtins, exception_type):
                exception = getattr(builtins, exception_type)(*args)
            else:
                exception = Exception(*args)
            data.append(exception)
        else:
            data.append(item)

    return data
