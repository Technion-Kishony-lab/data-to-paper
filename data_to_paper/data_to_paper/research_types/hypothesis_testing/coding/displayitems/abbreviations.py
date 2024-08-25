import re

P_VALUE_STRINGS = ('P>|z|', 'P-value', 'P>|t|', 'P>|F|')
KNOWN_ABBREVIATIONS = ('std', 'BMI', 'Std.', 'Std', 'Err.', 'Avg.', 'Coef.', 'SD', 'SE', 'CI') \
                      + P_VALUE_STRINGS


def contains_both_letter_and_numbers(name: str) -> bool:
    """
    Check if the name contains both letters and numbers.
    """
    return any(char.isalpha() for char in name) and any(char.isdigit() for char in name)


def is_unknown_abbreviation(name: str) -> bool:
    """
    Check if the name is abbreviated.
    """
    if not isinstance(name, str):
        return False

    if len(name) == 0:
        return False

    if name.isnumeric():
        return False

    if name in KNOWN_ABBREVIATIONS:
        return False

    if len(name) <= 2:
        return True

    for abbreviation in KNOWN_ABBREVIATIONS:
        if abbreviation.endswith('.'):
            pattern = r'\b' + re.escape(abbreviation)
        else:
            pattern = r'\b' + re.escape(abbreviation) + r'\b'
        name = re.sub(pattern, '', name)

    # if there are no letters left, it is not an abbreviation
    if not any(char.isalpha() for char in name):
        return False

    words = re.split(pattern=r'[-_ =(),]', string=name)
    if any(contains_both_letter_and_numbers(word) for word in words):
        return True

    # if there are over 3 words, it is not an abbreviation:
    if len(re.split(pattern=r' ', string=name)) >= 3:
        return False

    if '.' in name or ':' in name or '_' in name:
        return True
    words = re.split(pattern=r'[-_ ]', string=name)
    words = [word for word in words if word != '']
    if all((word.islower() or word.istitle()) for word in words):
        return False
    return True
