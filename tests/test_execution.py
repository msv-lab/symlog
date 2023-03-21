from symlog.souffle import run_program, parse
from symlog.utils import read_file
from symlog.helper import format_output
import pickle
from deepdiff import DeepDiff


def test_run0():
    program = parse(read_file('tests/data/programs/program1.dl'))
    relations = run_program(program, dict())
    formatted_output = format_output(program, relations)
    expected_output = {"correct_usage(('1',))": ""}
    
    diff = DeepDiff(formatted_output, expected_output)
    assert not diff, f"Expected no difference, but found: {diff}"


def test_run1():
    program = parse(read_file('tests/data/programs/program1_trans.dl'))
    relations = run_program(program, dict())
    formatted_output = format_output(program, relations)

    with open("tests/data/programs/program1_trans_output.pickle", "rb") as f:
        expected_output = pickle.load(f)

    diff = DeepDiff(formatted_output, expected_output)
    assert not diff, f"Expected no difference, but found: {diff}"


def test_run2():
    program = parse(read_file('tests/data/programs/program2_trans.dl'))
    relations = run_program(program, dict())
    formatted_output = format_output(program, relations)

    with open('tests/data/programs/program2_trans_output.pickle', 'rb') as f:
        expected_output = pickle.load(f)

    diff = DeepDiff(formatted_output, expected_output)
    assert not diff, f"Expected no difference, but found: {diff}"


def test_run3():
    program = parse(read_file('tests/data/programs/program3_trans.dl'))
    relations = run_program(program, dict())
    formatted_output = format_output(program, relations)

    with open('tests/data/programs/program3_trans_output.pickle', 'rb') as f:
        expected_output = pickle.load(f)

    diff = DeepDiff(formatted_output, expected_output)
    assert not diff, f"Expected no difference, but found: {diff}"

