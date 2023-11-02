from typing import Callable
from symlog.common import (
    CONTAINS,
    DOES_NOT_CONTAIN,
)
from itertools import combinations
from more_itertools import unique_everseen
from symlog.utils import is_sublist


def ddmin(
    test_function: Callable,
    input: list,
    raise_on_error,
) -> list:
    """
    Delta debugging algorithm.
    :param test: The test function.
    :param input: The input facts.
    :param raise_on_error: If True, raise an error on invalid input. If False, returns None.
    :return: The minimized input facts.
    """

    if test_function(input) == DOES_NOT_CONTAIN:
        if raise_on_error:
            raise ValueError(f"The full {input} cannot pass the test function.")
        else:
            return None

    # the input is not needed to produce the target tuples
    if test_function([]) == CONTAINS:
        return []

    n = 2  # Initial granularity

    while len(input) >= 2:
        start = 0
        subset_length = int(len(input) / n)
        some_complement_is_failing = False

        while start < len(input):
            complement = input[: int(start)] + input[int(start + subset_length) :]

            if test_function(complement) == CONTAINS:
                input = complement
                n = max(n - 1, 2)
                some_complement_is_failing = True
                break

            start += subset_length

        if not some_complement_is_failing:
            if n == len(input):
                break
            n = min(n * 2, len(input))

    return input


def monotonic_all(provenance_function: Callable, input_list: list) -> list:
    """Final all minimized input facts that can produce the target output"""

    cached_results = []

    def previous_computed_result(input_data):
        for prev_result in list(unique_everseen(cached_results, key=tuple)):
            if is_sublist(prev_result, input_data):
                return prev_result
        return None

    def dfs(current_input_list):
        results = []

        # try to reuse the minimized input computed previously
        minimized_input = previous_computed_result(current_input_list)
        # if not, compute the minimal input
        if not minimized_input:
            minimized_input = provenance_function(input_list)

        if not minimized_input:
            return results

        results.append(minimized_input)
        cached_results.append(minimized_input)

        # get combinations of the minimized_input
        for comb, complement in combinations_and_complements(minimized_input):
            comb = list(comb)  # convert tuple to list
            new_input = comb + filter_out_excluded_items(current_input_list, complement)

            results.extend(dfs(new_input))

        return results

    # execute dfs and retrieve results
    all_results = dfs(input_list)

    # deduplicate results
    unique_results = list(unique_everseen(all_results, key=tuple))

    return unique_results


def ddmin_all_monotonic(
    test_function: Callable, input_list: list, raise_on_error=False
) -> list:
    """
    Find all minimized input facts that can produce the target
    outputs when monotonicity is guaranteed.
    :param test_function: The test function.
    :param input_list: The input facts.
    :return: The minimized input facts.
    """

    cached_results = []

    def previous_computed_result(input_data):
        for prev_result in list(unique_everseen(cached_results, key=tuple)):
            if is_sublist(prev_result, input_data):
                return prev_result
        return None

    def dfs(current_input):
        results = []

        # try to reuse the minimized input computed previously
        minimized_input = previous_computed_result(current_input)
        # if not, compute the minimal input
        if not minimized_input:
            minimized_input = ddmin(test_function, current_input, raise_on_error)

        if not minimized_input:
            return results

        results.append(minimized_input)
        cached_results.append(minimized_input)

        # get combinations of the minimized_input
        for comb, complement in combinations_and_complements(minimized_input):
            comb = list(comb)  # convert tuple to list
            new_input = comb + filter_out_excluded_items(current_input, complement)

            results.extend(dfs(new_input))

        return results

    # execute dfs and retrieve results
    all_results = dfs(input_list)

    # deduplicate results
    unique_results = list(unique_everseen(all_results, key=tuple))

    return unique_results


def filter_out_excluded_items(source_list, exclusion_list):
    # convert exclusion_list to a set for faster look-up
    exclusion_set = set(exclusion_list)

    # remove elements from source_list that are in exclusion_set
    return [item for item in source_list if item not in exclusion_set]


def combinations_and_complements(lst: list) -> list[tuple[tuple, tuple]]:
    all_combs_and_complements = []

    def get_complement(lst, comb):
        temp = lst.copy()
        for item in comb:
            temp.remove(item)
        return tuple(temp)

    for comb in combinations(lst, len(lst) - 1):
        complement = get_complement(lst, comb)
        all_combs_and_complements.append((comb, complement))

    # remove duplicate combinations and complements
    all_combs_and_complements = list(unique_everseen(all_combs_and_complements))

    return all_combs_and_complements
