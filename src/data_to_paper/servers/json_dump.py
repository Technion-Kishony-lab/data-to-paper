import json


def dump_to_json(serialized_data, filename):
    with open(filename, 'w') as file:
        json.dump(serialized_data, file, indent=4, sort_keys=False)


def load_from_json(filename):
    with open(filename, 'r') as file:
        return json.load(file)
