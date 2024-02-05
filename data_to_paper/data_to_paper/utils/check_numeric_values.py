import re
from typing import List, Optional, Tuple


def extract_numeric_values(text: str) -> List[str]:
    """
    Extract all the numeric values from the given text.
    """
    # use regex to extract all the numeric values:
    return re.findall(r"[+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?", text.replace('{,}', '').replace(',', ''))


def unify_representation_of_numeric_values(text: str) -> str:
    """
    Unify the representation of numeric values with scientific notation.
    For example:
    "4.32 \times 10^{-5}" -> 4.32e-5
    "4.32 \times 10^5" -> 4.32e5
    "23.7987 * 10^5" -> 23.7987e5
    "23.7987*10^{-5}" -> 23.7987e-5
    """

    # This function is used to format the matched groups into scientific notation
    def repl(m):
        base = float(m.group(1))
        exponent = int(m.group(2).replace('{', '').replace('}', ''))  # remove curly braces
        return f'{base}e{exponent}'

    # Create regex pattern for numbers in the specified format
    pattern = r"(\d+\.\d+)\s*\\times\s*10\^(\{?\-?\d+\}?)"  # \times version
    text = re.sub(pattern, repl, text)

    pattern = r"(\d+\.\d+)\s*\*\s*10\^(\{?\-?\d+\}?)"  # * version
    text = re.sub(pattern, repl, text)

    return text


def is_one_with_zeros(str_number: str) -> bool:
    """
    Check if the given string number is 1 with zeros before or after.
    Like 0.001, 0.1, 1, 10, 100, etc.
    """
    return str_number.lstrip('-').replace(',', '').replace('.', '').lstrip('0').rstrip('0') == '1'


def is_int_below_max(str_number: str, max_int: int) -> bool:
    """
    Check if the given string number is an int below the given max int.
    """
    return '.' not in str_number and ',' not in str_number and 'e' not in str_number.lower() \
        and abs(int(str_number)) < max_int


def round_to_n_digits(str_number: str, n_digits: int, remove_sign: bool = True) -> float:
    """
    Round the given number to the given number of digits.
    """
    number = float(str_number.replace(',', ''))
    rounded = float(f'{float(f"{number:.{n_digits}g}"):g}')
    if remove_sign:
        return abs(rounded)
    return rounded


def truncate_to_n_digits(str_number: str, n_digits: int, remove_sign: bool = True) -> float:
    """
    Truncate the given number to the given number of digits.
    1.237 -> 1.23  (n_digits=3)
    """
    str_number = str_number.replace(',', '')
    str_number, power = split_number_and_power(str_number)
    digit_count = 0
    is_leading_zero = True
    is_after_point = False
    for i in range(len(str_number)):
        digit = str_number[i]
        if digit == '-' or digit == '+':
            continue
        if digit == '.':
            is_after_point = True
            continue
        if is_leading_zero and digit != '0':
            is_leading_zero = False
        if not is_leading_zero:
            digit_count += 1
        if digit_count == n_digits:
            break
    if not is_after_point:
        power = power + len(str_number) - i - 1
    truncated = float(str_number[:i + 1]) * 10 ** power
    if remove_sign:
        return abs(truncated)
    return truncated


def is_after_smaller_than_sign(str_number: str, target: str) -> Optional[bool]:
    """
    Check if the given string number extracted from the target str appear after a '<' sign.
    """
    str_number_positions = [m.start() for m in re.finditer(re.escape(str_number), target)]
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
    str_number_positions = [m.start() for m in re.finditer(re.escape(str_number), target)]
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


def is_any_matching_value_after_rounding_to_n_digits(source_str_numbers: List[str], target_number: float,
                                                     n_digits: int) -> bool:
    """
    Check if there exists a number in the source that matches after rounding to the given number of digits.
    """
    any_match = \
        any(round_to_n_digits(source_number, n_digits) == target_number
            for source_number in source_str_numbers)
    # if a number ends with '5' we allow also rounding it upwards
    any_match = any_match or \
        any(round_to_n_digits(source_number[:-1] + '6', n_digits) == target_number
            for source_number in source_str_numbers if source_number.endswith('5'))
    return any_match


def is_any_matching_value_after_truncating_to_n_digits(source_str_numbers: List[str], target_number: float,
                                                       n_digits: int) -> bool:
    """
    Check if there exists a number in the source that matches after rounding to the given number of digits.
    """
    return any(truncate_to_n_digits(source_number, n_digits) == target_number
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


def split_number_and_power(str_number: str) -> Tuple[str, int]:
    if 'e' in str_number:
        str_number, power = str_number.split('e')
        power = int(power)
    else:
        power = 0
    return str_number, power


def is_number_legit(str_number: str,
                    ignore_int_below: int = 0,
                    ignore_one_with_zeros: bool = True,
                    special_numbers_to_ignore: List[str] = ('95', '99', '100', '1.96', '0.05'),
                    ) -> bool:
    """
    Check if the given string number is ok even if not found in the source.
    """
    if ignore_int_below and is_int_below_max(str_number, ignore_int_below):
        return True

    # we do not check numbers like 1, 0.1, 0.01, etc., or 1, 10, 100, etc.:
    if ignore_one_with_zeros and is_one_with_zeros(str_number):
        return True

    # check if the string number is a special number that we want to ignore:
    if str_number.strip('-').strip('+') in special_numbers_to_ignore:
        return True


def find_non_matching_numeric_values(source: str, target: str, ignore_int_below: int = 0,
                                     remove_trailing_zeros: bool = False,
                                     ignore_one_with_zeros: bool = True,
                                     ignore_after_smaller_than_sign: bool = True,
                                     special_numbers_to_ignore: List[str] = ('95', '99', '100', '1.96', '0.05'),
                                     allow_truncating: bool = True) -> Tuple[List[str], List[str]]:
    """
    Check that all the numerical values mentioned in the target are also mentioned in the source.
    For each numerical value in the target, we check that there exists a numeric values in the source
    that matches after rounding to the same number of digits.
    """

    target = unify_representation_of_numeric_values(target)
    source = unify_representation_of_numeric_values(source)

    str_target_numbers = extract_numeric_values(target)
    str_source_numbers = extract_numeric_values(source)

    non_matching_str_numbers = []
    matching_str_numbers = []
    for str_target_number in str_target_numbers:
        original_str_target_number = str_target_number

        str_target_number = str_target_number.lower()

        if is_number_legit(str_target_number, ignore_int_below, ignore_one_with_zeros, special_numbers_to_ignore):
            continue

        # check if the string number appears after a '<' sign:
        if ignore_after_smaller_than_sign and is_after_smaller_than_sign(str_target_number, target):
            continue

        str_target_number, power = split_number_and_power(str_target_number)

        num_digits = get_number_of_significant_figures(str_target_number, remove_trailing_zeros)

        for should_truncate in range(allow_truncating + 1):

            target_number = round_to_n_digits(str_target_number, num_digits) * 10 ** power
            target_number_if_percent = round(target_number / 100, 10)  # round is just for python float precision

            # check that there exists a number in the source that matches after rounding to the same number of digits:
            if should_truncate:
                is_match_as_is = is_any_matching_value_after_truncating_to_n_digits(
                    str_source_numbers, target_number, num_digits)
                is_match_100 = is_any_matching_value_after_truncating_to_n_digits(
                    str_source_numbers, target_number_if_percent, num_digits)
            else:
                is_match_as_is = is_any_matching_value_after_rounding_to_n_digits(
                    str_source_numbers, target_number, num_digits)
                is_match_100 = is_any_matching_value_after_rounding_to_n_digits(
                    str_source_numbers, target_number_if_percent, num_digits)

            # for now, we assume that any number might be a percentage, setting to None:
            is_target_percentage = None  # is_percentage(str_target_number, target)

            if is_target_percentage is None:  # maybe percentage
                is_match = is_match_as_is or is_match_100
            elif is_target_percentage:  # percentage
                is_match = is_match_100
            else:  # not percentage
                is_match = is_match_as_is
            if is_match:
                matching_str_numbers.append(original_str_target_number)
                break
        else:
            non_matching_str_numbers.append(original_str_target_number)

    return non_matching_str_numbers, matching_str_numbers
