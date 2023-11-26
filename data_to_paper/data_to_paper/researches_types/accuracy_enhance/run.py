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


def is_perfect(number: int) -> bool:
    # return is_prime(number) and number % 10 == 7
    digits = [int(digit) for digit in str(number)]
    return is_prime(number) and digits[-1] == 7


def check_list_is_ok(numbers: List[int], start: int, end: int) -> Tuple[int, int, int, int]:
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


START, END = 100, 200
TOTAL_ATTEMPTS = 7
TOTAL_RUNS = 20
WITH_REVIEW = False
key_name = 'perfect_numbers'
perfect_definition = 'prime numbers whose last digit is 7'
order_name = 'reverse' if START > END else 'correct'

scores = np.zeros([TOTAL_RUNS, TOTAL_ATTEMPTS, 4])

for run in range(TOTAL_RUNS):
    converser = PythonDictWithDefinedKeysReviewBackgroundProductsConverser(
        web_conversation_name=None,
        max_reviewing_rounds=TOTAL_ATTEMPTS if WITH_REVIEW else 0,
        actions_and_conversations=ActionsAndConversations(),
        requested_keys=(key_name, ),
        value_type=Dict[str, List[int]],
        json_mode=True,
        model_engine=ModelEngine.GPT4_TURBO,
        goal_noun=f"a list of all 'perfect numbers' between {START} and {END}",
        goal_verb='create',
        system_prompt=f"You are a helpful assistant. We define 'perfect numbers' as {perfect_definition}.",
        user_initiation_prompt='Create {goal_noun}.\n'
                               f'Return a JSON object with a single key "{key_name}" mapping to the list.',
        other_system_prompt='You are a helpful assistant. You will need to check {goal_noun}.',
        sentence_to_add_at_the_end_of_performer_response=dedent_triple_quote_str("""
            Please check my list. Return a JSON object with the following keys:
            "missing": a list of all missing numbers
            "not_ok": a list of all numbers that are not ok
            "wrong_order": a list of all numbers that are not in the correct order
            "out_of_range": a list of all numbers that are out of range
            
            The lists should be empty if there are no such mistakes.
            """),
    )
    converser.initialize_dialog()
    for attempt in range(TOTAL_ATTEMPTS):
        response, cycle_status = converser.run_one_cycle()
        result = converser.get_valid_result()
        numbers = result[key_name]
        number_of_non_primes, number_of_missing_primes, number_of_wrong_order, number_of_out_of_range = \
            check_list_is_ok(numbers, START, END)
        print(f"### Run {run}, attempt {attempt} ### "
              f"Not ok: {number_of_non_primes}, Missing: {number_of_missing_primes}, "
              f"Wrong order: {number_of_wrong_order}, Out of range: {number_of_out_of_range}")
        if not WITH_REVIEW:
            converser.apply_append_user_message(dedent_triple_quote_str(f"""
                Check your list:
                * All numbers should be 'perfect numbers'.
                * Did you miss any 'perfect numbers'?
                * Numbers should be in the correct order and in the correct range.
                If you see problems, please fix the list. 
                If you think your list is correct, please return the same list again.
                Return a JSON object with a single key "{key_name}" mapping to the correct list.
                """))
        scores[run, attempt, :] = \
            number_of_non_primes, number_of_missing_primes, number_of_wrong_order, number_of_out_of_range
        if WITH_REVIEW and cycle_status is not CycleStatus.NOT_APPROVED_BY_OTHER:
            break
        if attempt > 0:
            converser.apply_delete_messages([-3, -4])
    scores[run, attempt + 1:, :] = scores[run, attempt:attempt + 1, :]

    np.save(f'scores_{TOTAL_RUNS}_runs_{TOTAL_ATTEMPTS}_attempts_primes_{START}_{END}_review_{int(WITH_REVIEW)}.npy', scores)


plt.figure(figsize=(10, 5))
plt.plot(np.arange(TOTAL_ATTEMPTS), np.mean(scores, axis=0))
plt.legend(['Non-primes', 'Missing primes', 'Wrong order', 'Out of range'])
plt.xlabel('Attempt')
plt.ylabel('Number of errors')
plt.title('Number of errors in each attempt')
plt.show()
