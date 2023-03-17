from core.souffle import run_program, parse
from core.utils import read_file
import pickle
from deepdiff import DeepDiff


def test_run0():
    program = parse(read_file('tests/data/program/program1.dl'))
    relations = run_program(program, dict())

    expected_relations = {'correct_usage': [['1']]}
    diff = DeepDiff(relations, expected_relations)
    
    assert not diff, f"Expected no difference, but found: {diff}"


def test_run1():
    program = parse(read_file('tests/data/program/program1_trans.dl'))
    relations = run_program(program, dict())

    expected_relations = {'correct_usage': [['1', '-9223372036854775806'], ['1', '1'], ['1', '4'], ['1', '5']]}    
    diff = DeepDiff(relations, expected_relations)

    assert not diff, f"Expected no difference, but found: {diff}"


def test_run2():
    program = parse(read_file('tests/data/program/program2_trans.dl'))
    relations = run_program(program, dict())

    with open('tests/data/program/program2_trans_output.pickle', 'rb') as f:
        expected_relations = pickle.load(f)
    diff = DeepDiff(relations, expected_relations)
    
    assert not diff, f"Expected no difference, but found: {diff}"


def test_run3():
    program = parse(read_file('tests/data/program/program3_trans.dl'))
    relations = run_program(program, dict())

    with open('tests/data/program/program3_trans_output.pickle', 'rb') as f:
        expected_relations = pickle.load(f)
    diff = DeepDiff(relations, expected_relations)

    assert not diff, f"Expected no difference, but found: {diff}"


if '__main__' == __name__:
    test_run1()