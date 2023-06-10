import re
from typing import List, Optional, Tuple


def extract_numeric_values(text: str) -> List[str]:
    """
    Extract all the numeric values from the given text.
    """
    # use regex to extract all the numeric values:
    return re.findall(r"[+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?", text.replace('{,}', '').replace(',', ''))


def is_one_with_zeros(str_number: str) -> bool:
    """
    Check if the given string number is 1 with zeros before or after.
    Like 0.001, 0.1, 1, 10, 100, etc.
    """
    return str_number.replace(',', '').replace('.', '').lstrip('0').rstrip('0') == '1'


def is_int_below_max(str_number: str, max_int: int) -> bool:
    """
    Check if the given string number is an int below the given max int.
    """
    return '.' not in str_number and ',' not in str_number \
        and abs(int(str_number)) < max_int


def round_to_n_digits(str_number: str, n_digits: int) -> float:
    """
    Round the given number to the given number of digits.
    """
    number = float(str_number.replace(',', ''))
    return float(f'{float(f"{number:.{n_digits}g}"):g}')


def is_after_smaller_than_sign(str_number: str, target: str) -> Optional[bool]:
    """
    Check if the given string number extracted from the target str appear after a '<' sign.
    """
    str_number_positions = [m.start() for m in re.finditer(str_number, target)]
    for str_number_position in str_number_positions:
        if str_number_position > 0 and target[str_number_position - 1] == '<' or \
                str_number_position > 1 and target[str_number_position - 2] == '<':
            return True
    return False


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


def is_any_matching_value_up_to_n_digits(source_str_numbers: List[str], target_number: float, n_digits: int
                                         ) -> bool:
    """
    Check if there exists a number in the source that matches after rounding to the given number of digits.
    """
    return any(round_to_n_digits(source_number, n_digits) == target_number
               for source_number in source_str_numbers)


def get_number_of_significant_figures(str_number: str, remove_trailing_zeros: bool = True) -> int:
    """
    Get the number of significant figures in the given string number.
    """
    digits = str_number.replace('.', '').replace(',', '').replace('-', '')
    # remove leading zeros:
    digits = digits.lstrip('0')

    # remove trailing zeros:
    if remove_trailing_zeros:
        digits = digits.rstrip('0')

    return len(digits)


def add_one_to_last_digit(num_str):
    num_list = list(num_str)  # Convert string to list for easy modification
    carry = 1
    for i in range(len(num_list) - 1, -1, -1):
        if num_list[i].isdigit():
            if num_list[i] == '9' and carry == 1:
                num_list[i] = '0'  # Carry the increment over to the next digit
            else:
                num_list[i] = str(int(num_list[i]) + carry)  # Add the increment
                carry = 0  # Reset the carry
        if carry == 0:  # No need to go further if there's no carry
            break
    if carry == 1:  # If there's still a carry, prepend it to the list
        num_list = ['1'] + num_list
    return ''.join(num_list)


def find_non_matching_numeric_values(source: str, target: str, ignore_int_below: int = 0,
                                     remove_trailing_zeros: bool = False,
                                     ignore_one_with_zeros: bool = True,
                                     ignore_after_smaller_than_sign: bool = True,
                                     allow_truncating: bool = True) -> Tuple[List[str], List[str]]:
    """
    Check that all the numerical values mentioned in the target are also mentioned in the source.
    For each numerical value in the target, we check that there exists a numeric values in the source
    that matches after rounding to the same number of digits.
    """

    str_target_numbers = extract_numeric_values(target)
    str_source_numbers = extract_numeric_values(source)

    non_matching_str_numbers = []
    matching_str_numbers = []
    for str_target_number in str_target_numbers:

        if ignore_int_below and is_int_below_max(str_target_number, ignore_int_below):
            continue

        # we do not check numbers like 1, 0.1, 0.01, etc., or 1, 10, 100, etc.:
        if ignore_one_with_zeros and is_one_with_zeros(str_target_number):
            continue

        # check if the string number appears after a '<' sign:
        if ignore_after_smaller_than_sign and is_after_smaller_than_sign(str_target_number, target):
            continue

        num_digits = get_number_of_significant_figures(str_target_number, remove_trailing_zeros)

        for should_truncate in range(allow_truncating + 1):
            if should_truncate:
                to_check = add_one_to_last_digit(str_target_number)
            else:
                to_check = str_target_number

            target_number = round_to_n_digits(to_check, num_digits)

            # check that there exists a number in the source that matches after rounding to the same number of digits:
            is_match_as_is = is_any_matching_value_up_to_n_digits(str_source_numbers, target_number, num_digits)
            is_match_100 = is_any_matching_value_up_to_n_digits(str_source_numbers, round(target_number / 100, 10),
                                                                num_digits)

            # for now, we assume that any number might be a percentage, setting to None:
            is_target_percentage = None  # is_percentage(str_target_number, target)

            if is_target_percentage is None:  # maybe percentage
                is_match = is_match_as_is or is_match_100
            elif is_target_percentage:  # percentage
                is_match = is_match_100
            else:  # not percentage
                is_match = is_match_as_is
            if is_match:
                matching_str_numbers.append(str_target_number)
                break
        else:
            non_matching_str_numbers.append(str_target_number)

    return non_matching_str_numbers, matching_str_numbers


"""
Formulas
to allow chatgpt to add numbers that are calculated from the context, we provide a formula pattern:
"The difference between x and y was [12345 - 12300 = 45]"
"""


def remove_equal_sign_and_result(string):
    return re.sub(r'\[(.*?) = (.*?)\]', r"[\1]", string)


def get_all_formulas(string):
    return re.findall(r'\[[^\]]+?\]', string)
