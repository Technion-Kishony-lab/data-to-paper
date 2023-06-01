import re
from typing import List


def extract_numeric_values(text: str) -> List[str]:
    """
    Extract all the numeric values from the given text.
    """
    # use regex to extract all the numeric values:
    return re.findall(r"[-+]?\d*\.\d+|\d+", text)


def round_to_n_digits(number: float, n_digits: int) -> float:
    """
    Round the given number to the given number of digits.
    """
    return float(f'{float(f"{number:.{n_digits}g}"):g}')


def find_non_matching_numeric_values(source: str, target: str) -> List[str]:
    """
    Check that all the numerical values mentioned in the target are also mentioned in the source.
    For each numerical value in the target, we check that there exists a numeric values in the source
    that matches after rounding to the same number of digits.
    """

    str_target_numbers = extract_numeric_values(target)
    str_source_numbers = extract_numeric_values(source)

    non_matching_str_numbers = []
    for str_target_number in str_target_numbers:
        num_digits = len(str_target_number.replace('.', ''))
        target_number = round_to_n_digits(float(str_target_number), num_digits)
        # check that there exists a number in the source that matches after rounding to the same number of digits:
        is_match = any(round_to_n_digits(float(str_source_number), num_digits) == target_number
                       for str_source_number in str_source_numbers)
        if not is_match:
            non_matching_str_numbers.append(str_target_number)
    return non_matching_str_numbers
