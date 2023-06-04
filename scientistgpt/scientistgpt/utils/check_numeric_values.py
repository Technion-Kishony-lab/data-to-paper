import re
from typing import List, Optional


def extract_numeric_values(text: str) -> List[str]:
    """
    Extract all the numeric values from the given text.
    """
    # use regex to extract all the numeric values:
    return re.findall(r"[-+]?\b\d+(?:,\d+)*(?:\.\d+)?\b", text)


def round_to_n_digits(str_number: str, n_digits: int) -> float:
    """
    Round the given number to the given number of digits.
    """
    number = float(str_number.replace(',', ''))
    return float(f'{float(f"{number:.{n_digits}g}"):g}')


def is_percentage(str_number: str, target: str, search_distance: int = 30) -> Optional[bool]:
    """
    Check if the given string number extracted from the target str is a percentage.
    True: if the string matches a string in the target the ends with '%' (in the target).
    Nane: (maybe percentage) if the word 'percent'/'percentage' appears up to search_distance characters before/after
    the string number.
    False: otherwise
    """
    target_words = target.split()
    # find all the occurrences of the string number in the target:
    str_number_positions = [m.start() for m in re.finditer(str_number, target)]
    len_str_number = len(str_number)

    # check if the string number is a percentage:
    for str_number_position in str_number_positions:
        # check if the string number is a percentage (ends with '%'):
        if str_number_position + len_str_number < len(target) and target[str_number_position + len_str_number] == '%':
            return True
        # check if the string number is a maybe percentage
        # (the word 'percent'/'percentage' appears up to search_distance characters before/after the string number):
        for keyword in ['percent', 'percentage']:
            if keyword in target_words[max(0, str_number_position - search_distance):
                                       str_number_position + len_str_number + search_distance]:
                return None
    return False


def is_any_matching_numeric_value_up_to_n_digits(source_str_numbers: List[str], target_number: float, n_digits: int
                                                 ) -> bool:
    """
    Check if there exists a number in the source that matches after rounding to the given number of digits.
    """
    return any(round_to_n_digits(source_number, n_digits) == target_number
               for source_number in source_str_numbers)


def get_number_of_significant_figures(str_number: str) -> int:
    """
    Get the number of significant figures in the given string number.
    """
    digits = str_number.replace('.', '').replace(',', '').replace('-', '')
    # remove leading zeros:
    digits = digits.lstrip('0')
    return len(digits)


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
        num_digits = get_number_of_significant_figures(str_target_number)
        target_number = round_to_n_digits(str_target_number, num_digits)
        # check that there exists a number in the source that matches after rounding to the same number of digits:

        is_match_as_is = is_any_matching_numeric_value_up_to_n_digits(str_source_numbers, target_number, num_digits)
        is_match_100 = is_any_matching_numeric_value_up_to_n_digits(str_source_numbers, target_number / 100, num_digits)
        is_target_percentage = is_percentage(str_target_number, target)
        if is_target_percentage is None:  # maybe percentage
            is_match = is_match_as_is or is_match_100
        elif is_target_percentage:  # percentage
            is_match = is_match_100
        else:  # not percentage
            is_match = is_match_as_is
        if not is_match:
            non_matching_str_numbers.append(str_target_number)
    return non_matching_str_numbers
