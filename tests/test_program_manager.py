import pytest
from symlog.souffle import (
    String,
    Number,
    Variable,
    SymbolicString,
    SymbolicNumber,
    Literal,
    Rule,
    NUM,
    SYM,
)
from symlog.common import SYMLOG_NUM_POOL, SYMBOLIC_CONSTANT_PREFIX, UNK_TYPE
from symlog.environment import get_env, Environment
from symlog.utils import check_equality


def test_string():
    # Test the String method
    manager = get_env().program_manager
    string = manager.String("foo")
    assert string.value == "foo"


def test_number():
    # Test the Number method
    manager = get_env().program_manager
    number = manager.Number(1)
    assert number.value == 1


def test_variable():
    # Test the Variable method
    manager = get_env().program_manager
    variable = manager.Variable("x")
    assert variable.name == "x"


def test_symbolic_string():
    # Test the SymbolicString method
    with Environment() as env:
        manager = env.program_manager
        symbolic_string = manager._get_symbolic_string("foo")
        assert symbolic_string.name == f"{SYMBOLIC_CONSTANT_PREFIX}1"
        assert manager.symbols["foo"] == symbolic_string


def test_symbolic_string_without_name():
    # Test the SymbolicString method without a name
    with Environment() as env:
        manager = env.program_manager
        symbolic_string = manager._get_symbolic_string()
        assert symbolic_string.name == f"{SYMBOLIC_CONSTANT_PREFIX}1"


def test_symbolic_string_with_existing_name():
    # Test the SymbolicString method with an existing name
    with Environment() as env:
        manager = env.program_manager
        symbolic_string = manager._get_symbolic_string("foo")
        with pytest.raises(ValueError):
            symbolic_string2 = manager._get_symbolic_string("foo")


def test_symbolic_number():
    # Test the SymbolicNumber method
    with Environment() as env:
        manager = env.program_manager
        symbolic_number = manager._get_symbolic_number("foo")
        assert symbolic_number.name == SYMLOG_NUM_POOL[1]
        assert manager.symbols["foo"] == symbolic_number


def test_symbolic_number_without_name():
    # Test the SymbolicNumber method without a name
    with Environment() as env:
        manager = env.program_manager
        symbolic_number = manager._get_symbolic_number()
        assert symbolic_number.name == SYMLOG_NUM_POOL[1]


def test_symbolic_number_with_existing_name():
    # Test the SymbolicNumber method with an existing name
    with Environment() as env:
        manager = env.program_manager
        symbolic_number = manager._get_symbolic_number("foo")
        with pytest.raises(ValueError):
            symbolic_number2 = manager._get_symbolic_number("foo")


def test_literal():
    # Test the Literal method
    with Environment() as env:
        manager = env.program_manager
        literal = manager.Literal("foo", [Variable("x"), Number(1)], True)
        assert literal.name == "foo"
        assert literal.args == [Variable("x"), Number(1)]
        assert literal.positive is True


def test_fact():
    # Test the Fact method
    with Environment() as env:
        manager = env.program_manager
        fact = manager.Fact("foo", [String("x"), Number(1)])
        assert isinstance(fact, Rule)
        assert fact.head.name == "foo"
        assert fact.head.args == [String("x"), Number(1)]
        assert fact.head.positive is True
        assert fact.body == []
        assert fact in manager.facts


def test_rule():
    # Test the Rule method
    with Environment() as env:
        manager = env.program_manager
        head = manager.Literal("foo", [Variable("x"), Number(1)], True)
        body = [
            manager.Literal("bar", [Variable("x"), Number(1)], True),
            manager.Literal("baz", [Variable("y"), Number(2)], False),
        ]
        rule = manager.Rule(head, body)
        assert isinstance(rule, Rule)
        assert rule.head == head
        assert rule.body == body
        assert rule in manager.rules


def test_program():
    # Test the Program method
    with Environment() as env:
        manager = env.program_manager
        head = manager.Literal("foo", [Variable("x"), Number(1)], True)
        body = [
            manager.Literal("bar", [Variable("x"), Number(1)], True),
            manager.Literal("baz", [Variable("y"), Number(2)], False),
        ]
        rule = manager.Rule(head, body)
        program = manager.program
        assert program.relation_decls == {
            "foo": [UNK_TYPE, NUM],
            "bar": [UNK_TYPE, NUM],
            "baz": [UNK_TYPE, NUM],
        }
        assert program.outputs == ["foo"]
        assert program.rules == [rule]
        assert program.facts == []


def test_create_subprogram():
    # Test creating a new program with fewer rules and facts

    with Environment() as env:
        manager = env.program_manager
        head = manager.Literal("foo1", [Variable("x"), Number(1)], True)
        body = [
            manager.Literal("bar", [Variable("x"), Number(1)], True),
            manager.Literal("baz", [Variable("y"), Number(2)], False),
        ]
        rule1 = manager.Rule(head, body)
        rule2 = manager.Rule(
            manager.Literal("foo2", [Variable("x"), Number(1)], True), body
        )
        program = manager.program
        new_program = manager.create_subprogram_copy([rule1], [])

        assert check_equality(new_program.rules, [rule1])
        assert check_equality(new_program.facts, [])
        assert check_equality(new_program.outputs, ["foo1"])

        assert check_equality(program.rules, [rule1, rule2])
        assert check_equality(program.facts, [])
        assert check_equality(program.outputs, ["foo1", "foo2"])
