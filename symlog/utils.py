import symlog.common as common
from symlog.souffle import (
    String,
    Number,
    Variable,
    SymbolicNumber,
    SymbolicString,
)

import itertools
from typing import List, Dict, Set, Any
from deepdiff import DeepDiff
from collections import Counter
from collections.abc import Iterable


def flatten_dict(d: Dict[Any, Set[Any] | List[Any]]) -> Dict[Any, Any]:
    return {k: remove_duplicates(list(itertools.chain(*v))) for k, v in d.items()}


def is_arg_symbolic_or_wildcard(arg) -> bool:
    # Returns True if the argument is a symbolic constant/number/binding variable or a wildcard '_'
    if isinstance(arg, (SymbolicString, SymbolicNumber)):
        return True
    elif isinstance(arg, Variable):
        return arg.name.startswith(common.BINDING_VARIABLE_PREFIX)
    elif isinstance(arg, str) and arg == "_":
        return True
    elif isinstance(arg, str) and not is_number(arg):
        return arg.startswith(common.SYMBOLIC_CONSTANT_PREFIX)
    elif isinstance(arg, str) and is_number(arg):
        return int(arg) in common.SYMLOG_NUM_POOL
    else:
        return False


def is_arg_symbolic(arg) -> bool:
    """Returns True if the argument is a symbolic constant/number"""
    if isinstance(arg, String) and arg.value.startswith(
        common.SYMBOLIC_CONSTANT_PREFIX
    ):
        return True
    elif isinstance(arg, Number) and arg.value in common.SYMLOG_NUM_POOL:
        return True
    elif isinstance(arg, SymbolicString) or isinstance(arg, SymbolicNumber):
        return True
    elif isinstance(arg, str) and arg.startswith(common.SYMBOLIC_CONSTANT_PREFIX):
        return True
    elif isinstance(arg, str) and is_number(arg) and int(arg) in common.SYMLOG_NUM_POOL:
        return True
    elif isinstance(arg, int) and arg in common.SYMLOG_NUM_POOL:
        return True
    else:
        return False


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def is_sublist(list1, list2) -> bool:
    """Returns True if list1 is a sublist of list2"""
    return all(item in list2 for item in list1)


def remove_duplicates(lst):
    unique_list = []
    [unique_list.append(x) for x in lst if x not in unique_list]
    return unique_list


def check_equality(lst1, lst2, ignore_order=False):
    diff = DeepDiff(lst1, lst2, ignore_order=ignore_order)
    return diff == {}


def flatten_lists_only(lst):
    for item in lst:
        if isinstance(item, list):
            yield from item  # Flatten the list
        else:
            yield item  # Yield other items


def divide_list_by_subslit(all_facts, sub_facts):
    """
    Splits all_facts into two lists based on sub_facts: a list of facts found in sub_facts (up to the occurrence
    count in all_facts) and a list of facts not found in sub_facts.

    Note:
        The returned sub_facts list represents the intersection of all_facts and input sub_facts, limited by
        the occurrence count in all_facts.

        Example:
            If all_facts is ['a', 'b', 'c', 'a', 'b', 'c'] and sub_facts is ['a', 'b', 'a', 'a'],
            the returned sub_facts will be ['a', 'a', 'b'].

    Args:
        all_facts (list): The main list of facts.
        sub_facts (list): A sublist of facts.

    Returns:
        tuple: A tuple containing two lists - non_sub_facts and sub_facts.
    """
    # count occurrences of each fact
    all_facts_counter = Counter(all_facts)
    sub_facts_counter = Counter(sub_facts)

    non_sub_facts = []
    sub_facts = []

    # process each fact in all_facts
    for fact, count in all_facts_counter.items():
        # determine the count of this fact in sub_facts and non_sub_facts
        min_count = min(count, sub_facts_counter[fact])
        sub_facts.extend([fact] * min_count)
        non_sub_facts.extend([fact] * (count - min_count))

    return non_sub_facts, sub_facts


def is_namedtuple_instance(x):
    _is_namedtuple = isinstance(x, tuple) and hasattr(x, "_fields")
    return _is_namedtuple


def recursive_flatten(lst):
    for item in lst:
        if (
            isinstance(item, Iterable)
            and not is_namedtuple_instance(item)
            and not isinstance(item, str)
        ):
            yield from recursive_flatten(item)
        else:
            yield item
