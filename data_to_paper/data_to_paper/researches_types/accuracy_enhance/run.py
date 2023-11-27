from typing import List, Dict, Tuple, Callable

import numpy as np
import matplotlib.pyplot as plt

from data_to_paper.base_steps import PythonDictWithDefinedKeysReviewBackgroundProductsConverser, \
    PythonValueReviewBackgroundProductsConverser
from data_to_paper.conversation.actions_and_conversations import ActionsAndConversations
from data_to_paper.servers.openai_models import ModelEngine
from data_to_paper.utils import dedent_triple_quote_str


def is_prime(number: int) -> bool:
    """Returns whether the given number is prime."""
    if number < 2:
        return False
    for j in range(2, number):
        if number % j == 0:
            return False
    return True


def is_prime_and_sum_digits_divisible_by_7(number: int) -> bool:
    """a prime number whose sum of digits is divisible by 7 (e.g., 7, 43, 59, 61)"""
    digits = [int(digit) for digit in str(number)]
    return is_prime(number) and sum(digits) % 7 == 0


print([number for number in range(100) if is_prime_and_sum_digits_divisible_by_7(number)])


def is_prime_and_last_digit_is_7(number: int) -> bool:
    """a prime number whose last digit is 7 (e.g., 7, 17, 37, 47, 67, 97)"""
    return is_prime(number) and number % 10 == 7


print([number for number in range(100) if is_prime_and_last_digit_is_7(number)])


def check_list_is_ok(numbers: List[int], start: int, end: int, is_perfect: Callable) -> Tuple[int, int, int, int]:
    """
    Checks that the given list of numbers is a list of 'perfect' numbers between `start` and `end`.
    Returns the number of:
        (1) numbers that are not 'perfect'
        (2) 'perfect' numbers that are missing
        (3) numbers that are not in the correct order
        (4) numbers that are out of range.

    Note: if start > end, then the list should be in reverse order.
    """
    number_of_non_perfect = 0
    number_of_missing_perfect = 0
    number_of_wrong_order = 0
    number_of_out_of_range = 0
    is_reverse = start > end
    for i, number in enumerate(numbers):
        if not is_perfect(number):
            number_of_non_perfect += 1
        if number < min(start, end) or number > max(start, end):
            number_of_out_of_range += 1
        if i > 0:
            if (is_reverse and number > numbers[i - 1]) or (not is_reverse and number < numbers[i - 1]):
                number_of_wrong_order += 1
    for number in range(min(start, end), max(start, end) + 1):
        if is_perfect(number) and number not in numbers:
            number_of_missing_perfect += 1
    return number_of_non_perfect, number_of_missing_perfect, number_of_wrong_order, number_of_out_of_range


N_ATTEMPTS = 7
N_RUNS = 20
json_key = 'perfect_numbers'

for START, END in [(100, 200), (100, 400), (200, 100), (400, 100)]:
    for WITH_LIST in [True, False]:
        for DELETE_MESSAGES in [True, False]:
            for is_perfect in [is_prime_and_sum_digits_divisible_by_7, is_prime_and_last_digit_is_7]:

                print(f'\n\n' + '=' * 100 + f'\n'
                      f'### RANGE: {START}-{END}, WITH_LIST: {WITH_LIST}, DELETE_MESSAGES: {DELETE_MESSAGES}, '
                      f'\nIS_PERFECT: "{is_perfect.__doc__}"\n' + '=' * 100 + '\n')

                perfect_definition = is_perfect.__doc__
                order_name = 'descending' if START > END else 'ascending'
                list_str = f'\nConsider all numbers between {START} and {END}:\n{list(range(START, END + 1))}' \
                    if WITH_LIST else ''

                scores = np.zeros([N_RUNS, N_ATTEMPTS, 4])

                for run in range(N_RUNS):
                    converser = PythonDictWithDefinedKeysReviewBackgroundProductsConverser(
                        web_conversation_name=None,
                        max_reviewing_rounds=0,
                        actions_and_conversations=ActionsAndConversations(),
                        value_type=Dict[str, List[int]],
                        requested_keys=[json_key],
                        json_mode=True,
                        model_engine=ModelEngine.GPT4_TURBO,
                        goal_noun=f"a list of all perfect numbers between {START} and {END} in {order_name} order",
                        goal_verb='create',
                        system_prompt=f'You are a helpful assistant.\n' + list_str + '\n',
                        user_initiation_prompt=f"We define a 'perfect' number as {perfect_definition}.\n"
                                               'Create {goal_noun}.\n\n'
                                               f'Return JSON with a single key "{json_key}" '
                                               'mapped to your list of perfect numbers.\n\n'
                    )
                    converser.initialize_dialog()
                    for attempt in range(N_ATTEMPTS):
                        response, cycle_status = converser.run_one_cycle()
                        results = converser.get_valid_result()
                        numbers = results[json_key]
                        number_of_non_primes, number_of_missing_primes, number_of_wrong_order, number_of_out_of_range = \
                            check_list_is_ok(numbers, START, END, is_perfect)
                        print(f"### Run {run}, attempt {attempt} ### "
                              f"Not ok: {number_of_non_primes}, Missing: {number_of_missing_primes}, "
                              f"Wrong order: {number_of_wrong_order}, Out of range: {number_of_out_of_range}")
                        converser.apply_append_user_message(dedent_triple_quote_str(f"""
                            Check your list:
                            * are all numbers 'perfect'?
                            * did you possibly forget to include some 'perfect' numbers?
                            * are all numbers between {START} and {END}?
                            * is the list in {order_name} order?
                            
                            If you see problems, please correct the list. 
                            Return JSON with a single key "{json_key}" mapped to your list of perfect numbers.
                            
                            If you think your list is already correct, please return the same list again.
                            """))
                        scores[run, attempt, :] = \
                            number_of_non_primes, number_of_missing_primes, number_of_wrong_order, number_of_out_of_range
                        if attempt > 0 and DELETE_MESSAGES:
                            converser.apply_delete_messages([-3, -4])
                    scores[run, attempt + 1:, :] = scores[run, attempt:attempt + 1, :]

                np.save(f'set1_"{perfect_definition}"'
                        f'_{N_RUNS}_runs'
                        f'_{N_ATTEMPTS}_attempts'
                        f'_range_{START}_{END}'
                        f'_delete_{int(DELETE_MESSAGES)}'
                        f'_list_{int(WITH_LIST)}'
                        f'.npy', scores)


plt.figure(figsize=(10, 5))
plt.plot(np.arange(N_ATTEMPTS), np.mean(scores, axis=0))
plt.legend(['Non-primes', 'Missing primes', 'Wrong order', 'Out of range'])
plt.xlabel('Attempt')
plt.ylabel('Number of errors')
plt.title('Number of errors in each attempt')
plt.show()
