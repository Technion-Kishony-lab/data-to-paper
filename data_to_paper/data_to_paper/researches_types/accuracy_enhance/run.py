from typing import List, Dict, Tuple

import numpy as np
import matplotlib.pyplot as plt

from data_to_paper.base_steps import PythonDictWithDefinedKeysReviewBackgroundProductsConverser
from data_to_paper.base_steps.dual_converser import CycleStatus
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


def is_ok(number: int) -> bool:
    return is_prime(number)


def check_list_of_primes(numbers: List[int], start: int, end: int) -> Tuple[int, int, int, int]:
    """
    Checks that the given list of numbers is a list of prime numbers between start and end.
    Returns the number of numbers that are not prime, the number of primes that are missing,
    the number of numbers that are not in the correct order, and the number of numbers that are out of range.

    Note: if start > end, then the list should be in reverse order.
    """
    number_of_non_primes = 0
    number_of_missing_primes = 0
    number_of_wrong_order = 0
    number_of_out_of_range = 0
    is_reverse = start > end
    for i, number in enumerate(numbers):
        if not is_ok(number):
            number_of_non_primes += 1
        if number < min(start, end) or number > max(start, end):
            number_of_out_of_range += 1
        if i > 0:
            if (is_reverse and number > numbers[i - 1]) or (not is_reverse and number < numbers[i - 1]):
                number_of_wrong_order += 1
    for number in range(min(start, end), max(start, end) + 1):
        if is_ok(number) and number not in numbers:
            number_of_missing_primes += 1
    return number_of_non_primes, number_of_missing_primes, number_of_wrong_order, number_of_out_of_range


START = 1900
END = 500


total_attempts = 7
total_runs = 20
with_review = True

scores = np.zeros([total_runs, total_attempts, 4])

for run in range(total_runs):
    converser = PythonDictWithDefinedKeysReviewBackgroundProductsConverser(
        web_conversation_name=None,
        max_reviewing_rounds=total_attempts if with_review else 0,
        actions_and_conversations=ActionsAndConversations(),
        requested_keys=('primes',),
        value_type=Dict[str, List[int]],
        json_mode=True,
        model_engine=ModelEngine.GPT4_TURBO,
        goal_noun='list of prime numbers between {} and {}'.format(START, END),
        goal_verb='create',
        system_prompt="You are a helpful assistant.",
        user_initiation_prompt=dedent_triple_quote_str("""
            Return a JSON object with a single key "primes" mapping to a list of all prime numbers \
            between {start} and {end}, in reverse order.  
        """).format(start=START, end=END),
    )
    converser.initialize_dialog()
    for attempt in range(total_attempts):
        response, cycle_status = converser.run_one_cycle()
        result = converser.get_valid_result()
        numbers = result['primes']
        number_of_non_primes, number_of_missing_primes, number_of_wrong_order, number_of_out_of_range = \
            check_list_of_primes(numbers, START, END)
        print(f"----------- Run {run}, attempt {attempt}")
        print(f"Non-primes: {number_of_non_primes}, Missing primes: {number_of_missing_primes}, "
              f"Wrong order: {number_of_wrong_order}, Out of range: {number_of_out_of_range}")
        if not with_review:
            converser.apply_append_user_message(dedent_triple_quote_str("""
                Check your list. If you see problems, please fix them. 
                If you think your list is correct, please return it again.
                Return a JSON object with a single key "primes" mapping to the correct list.
                """))
        scores[run, attempt, :] = number_of_non_primes, number_of_missing_primes, number_of_wrong_order, \
            number_of_out_of_range
        if cycle_status is not CycleStatus.NOT_APPROVED_BY_OTHER:
            break

# dump the scores to a file
np.save(f'scores_{total_runs}_runs_{total_attempts}_attempts_primes_{START}_{END}_review_{int(with_review)}.npy', scores)


plt.figure(figsize=(10, 5))
plt.plot(np.arange(total_attempts), np.mean(scores, axis=0))
plt.legend(['Non-primes', 'Missing primes', 'Wrong order', 'Out of range'])
plt.xlabel('Attempt')
plt.ylabel('Number of errors')
plt.title('Number of errors in each attempt')
plt.show()
