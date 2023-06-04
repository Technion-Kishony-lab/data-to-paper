import re
import math
from typing import List


def extract_numeric_values(text: str) -> List[str]:
    """
    Extract all the numeric values from the given text.
    """
    # use regex to extract all the numeric values:
    return re.findall(r"[-+]?\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+", text)


def round_to_n_digits(str_number: str, n_digits: int) -> float:
    """
    Round the given number to the given number of digits.
    """
    number = float(str_number.replace(',', ''))
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
        target_number = round_to_n_digits(str_target_number, num_digits)
        # check that there exists a number in the source that matches after rounding to the same number of digits:
        if target_number <= 1:
            is_match = any(math.isclose(round_to_n_digits(float(source_number), num_digits),
                                        round_to_n_digits(float(target_number), num_digits), rel_tol=1e-5) or
                           math.isclose(round_to_n_digits(float(source_number), num_digits),
                                        round_to_n_digits(float(target_number*100), num_digits), rel_tol=1e-5)
                           for source_number in str_source_numbers)
        else:
            is_match = any(math.isclose(round_to_n_digits(float(source_number), num_digits),
                                        round_to_n_digits(float(target_number), num_digits), rel_tol=1e-5) or
                           math.isclose(round_to_n_digits(float(source_number), num_digits),
                                        round_to_n_digits(float(target_number)/100, num_digits), rel_tol=1e-5)
                           for source_number in str_source_numbers)
        if not is_match:
            non_matching_str_numbers.append(str_target_number)
    return non_matching_str_numbers
