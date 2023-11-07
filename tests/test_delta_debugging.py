from symlog import delta_debugging
import time
import random


# a monotonic test function
def my_input(input: list):
    # simulate the execution time
    time.sleep(0.01)
    if {1, 2}.issubset(set(input)):
        return delta_debugging.CONTAINS
    elif {2, 3}.issubset(set(input)):
        return delta_debugging.CONTAINS
    elif {3, 4}.issubset(set(input)):
        return delta_debugging.CONTAINS
    else:
        return delta_debugging.DOES_NOT_CONTAIN


# a monotonic test function
def my_input2(input: list):
    # simulate the execution time
    time.sleep(0.01)
    if {1, 30, 5, 70, 900, 1100, 5300, 7500, 9700}.issubset(set(input)):
        return delta_debugging.CONTAINS
    elif {2, 5}.issubset(set(input)):
        return delta_debugging.CONTAINS
    elif {4}.issubset(set(input)):
        return delta_debugging.CONTAINS
    else:
        return delta_debugging.DOES_NOT_CONTAIN


def my_input3(input_list: list, configurations: list):
    # simulate the execution time
    time.sleep(0.01)
    for configuration in configurations:
        if set(configuration).issubset(set(input_list)):
            return delta_debugging.CONTAINS

    return delta_debugging.DOES_NOT_CONTAIN


def have_same_elements(lst1, lst2):
    set1 = set(tuple(sorted(sublist)) for sublist in lst1)
    set2 = set(tuple(sorted(sublist)) for sublist in lst2)
    return set1 == set2


def test_ddmin():
    # Test case 1
    input_data = [1, 2, 4, 5]
    expected_output = [1, 2]
    assert delta_debugging.ddmin(my_input, input_data, False) == expected_output

    # Test case 2
    input_data = [1, 2, 3, 4, 5]
    possible_output = [[1, 2], [2, 3], [3, 4]]
    assert delta_debugging.ddmin(my_input, input_data, False) in possible_output

    # Test case 3
    input_data = [1, 2, 3, 4, 5]
    expected_output = [[1, 3, 5]]
    result = delta_debugging.ddmin(
        lambda input_list: my_input3(input_list, expected_output), input_data, False
    )
    assert result == expected_output[0]

    # Test case 4 (acceptable setting)
    random.seed(10)
    input_data = list(range(1000))
    expected_output = [list(random.sample(range(1, 1000), 15)) for _ in range(1)]
    print(f"expected_output: {expected_output}")
    result = delta_debugging.ddmin(
        lambda input_list: my_input3(input_list, expected_output), input_data, False
    )
    assert have_same_elements([result], expected_output)


def test_ddmin_all():
    # Test case 1
    input_data = [5, 5, 4, 4, 3, 3, 2, 2, 1]
    expected_output = [[1, 2], [2, 3], [3, 4]]
    result = delta_debugging.ddmin_all_monotonic(my_input, input_data)
    assert have_same_elements(result, expected_output)

    # Test case 2
    input_data = [1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 7, 8, 9, 10] + list(range(100))
    expected_output = [[1, 2], [2, 3], [3, 4]]
    result = delta_debugging.ddmin_all_monotonic(my_input, input_data)
    assert have_same_elements(result, expected_output)

    # Test case 3
    input_data = [1, 2, 2, 3, 3, 4, 4, 5, 6, 7, 7, 7, 8, 8, 9, 9, 10, 10, 10] + list(
        range(10000)
    )
    expected_output = [[1, 30, 5, 70, 900, 1100, 5300, 7500, 9700], [2, 5], [4]]
    result = delta_debugging.ddmin_all_monotonic(my_input2, input_data)
    assert have_same_elements(result, expected_output)

    # Test case 4 (acceptable setting)
    random.seed(10)
    input_data = list(range(1000))
    expected_output = [list(random.sample(range(1, 1000), 15)) for _ in range(2)]
    print(f"expected_output: {expected_output}")
    result = delta_debugging.ddmin_all_monotonic(
        lambda input_list: my_input3(input_list, expected_output), input_data
    )
    assert have_same_elements(result, expected_output)
