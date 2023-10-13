import pytest
from symlog.souffle import (
    Underscore,
    Variable,
    SymbolicNumber,
    SymbolicString,
    String,
    Number,
    Literal,
    Rule,
    SYM,
    NUM,
)
from symlog.environment import Environment


def test_check_literal_with_inconsistent_arg_type():
    # Test that a TypeError is raised if a literal has inconsisten argument type
    with Environment() as env:
        checker = env.syntax_checker
        literal1 = Literal("foo", [Number(1), Variable("y")], True)
        literal2 = Literal("foo", [String("x"), Variable("y")], True)
        with pytest.raises(TypeError):
            checker.check_literal(literal1)
            checker.check_literal(literal2)


def test_check_literal_with_inconsistent_arg_number():
    # Test that a TypeError is raised if a literal has inconsistent number of arguments
    with Environment() as env:
        checker = env.syntax_checker
        literal1 = Literal("foo", [Variable("x"), Variable("y")], True)
        literal2 = Literal("foo", [Variable("x")], True)
        checker.check_literal(literal1)
        with pytest.raises(TypeError):
            checker.check_literal(literal2)


def test_check_literal_with_valid_arg_type():
    # Test that no error is raised if a literal has a valid argument type
    with Environment() as env:
        checker = env.syntax_checker
        literal = Literal("foo", [Variable("x"), Variable("y")], True)
        checker.check_literal(literal)


def test_check_literal_with_consistent_arg_num():
    # Test that no error is raised if a literal has a consistent number of arguments
    with Environment() as env:
        checker = env.syntax_checker
        literal1 = Literal("foo", [Variable("x"), Variable("y")], True)
        literal2 = Literal("foo", [Variable("a"), Variable("b")], True)
        checker.check_literal(literal1)
        checker.check_literal(literal2)


def test_check_rule_with_underscore_in_head():
    # Test that a TypeError is raised if a rule has an underscore in its head
    with Environment() as env:
        checker = env.syntax_checker
        rule = Rule(Literal("foo", [Underscore(), Variable("y")], True), [])
        with pytest.raises(TypeError):
            checker.check_rule(rule)


def test_check_rule_with_ungrounded_variables():
    # Test that a TypeError is raised if a rule has ungrounded variables in its head
    with Environment() as env:
        checker = env.syntax_checker
        rule = Rule(
            Literal("foo", [Variable("x"), Variable("z")], True),
            [Literal("bar", [Variable("x"), Variable("y")], True)],
        )
        with pytest.raises(TypeError):
            checker.check_rule(rule)


def test_check_rule_with_negated_head():
    # Test that a TypeError is raised if a rule has a negated head
    with Environment() as env:
        checker = env.syntax_checker
        rule = Rule(Literal("foo", [Variable("x"), Variable("y")], False), [])
        with pytest.raises(TypeError):
            checker.check_rule(rule)


def test_check_fact_with_non_constant_args():
    # Test that a TypeError is raised if a fact has non-constant arguments
    with Environment() as env:
        checker = env.syntax_checker
        fact = Rule(Literal("foo", [Variable("x"), Variable("y")], True), [])
        with pytest.raises(TypeError):
            checker.check_fact(fact)


def test_check_fact_with_constant_args():
    # Test that no error is raised if a fact has constant arguments
    with Environment() as env:
        checker = env.syntax_checker
        fact = Rule(Literal("foo", [String("x"), Number(1)], True), [])
        checker.check_fact(fact)
