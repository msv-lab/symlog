from souffle import Program, Rule, Literal, run_program, collect, pprint, parse
from typing import List, Dict, Any
from transform_to_meta_program import transform_for_recording_facts
import utils

PASS = 0
FAIL = 1

def search(p: Program, transfromed_p: Program) -> List[Literal]:
    """Search for facts that cause some tuples to be derived via delta-debugging."""

    # extract original facts from the transformed meta program
    fact_names = set(map(lambda x: x.head.name, collect(
                        p, lambda x: isinstance(x, Rule) and not x.body)))
    # collect fact heads which are no longer 'facts' after transform_into_meta_program
    fact_heads = [fact.head for fact in collect(transfromed_p, lambda x: isinstance(
        x, Rule) and x.head.name in fact_names and x.body)]

    print(fact_names)

    # delta debugging
    n = 2

    transformed = transform_for_recording_facts(transfromed_p, n, fact_names)

    utils.store_file(pprint(transformed), "tests/transformed_record_program.dl")

    print("transformed program for recording facts is stored in tests/transformed_record_program.dl")

    # run program

def target_in_outputs(p: Program, input_facts: Dict, target_tuples: Dict) -> int:
    """Test whether the program p produces the target tuples."""

    # run program
    output_relations = run_program(p, input_facts)

    # check whether target tuples are derived
    derived = all(item in output_relations.items() for item in target_tuples.items())

    return FAIL if derived else PASS


def ddmin(test, inp, *test_args: Any):
    """Reduce the input inp, using the outcome of test(fun, inp)."""
    assert test(inp, *test_args) != PASS

    n = 2     # Initial granularity
    while len(inp) >= 2:
        start = 0
        subset_length = int(len(inp) / n)
        some_complement_is_failing = False

        while start < len(inp):
            complement = (inp[:int(start)] + inp[int(start + subset_length):])

            if test(complement, *test_args) == FAIL:
                inp = complement
                n = max(n - 1, 2)
                some_complement_is_failing = True
                break

            start += subset_length

        if not some_complement_is_failing:
            if n == len(inp):
                break
            n = min(n * 2, len(inp))

    return inp

if __name__ == "__main__":
    # load program
    p = parse(utils.read_file("tests/original_program.dl"))
    # load transformed program
    transfromed_p = parse(utils.read_file("tests/small_transformed_program.dl"))

    # search for facts that cause some tuples to be derived
    search(p, transfromed_p)
