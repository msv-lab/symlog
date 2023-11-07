import pytest

from symlog.souffle import Underscore
from symlog.shortcuts import (
    Variable,
    String,
    Number,
    Literal,
    Rule,
    Fact,
)
from symlog.syntax_checker import SyntaxChecker


def test_check_literal_with_inconsistent_arg_type():
    # Test that a TypeError is raised if a literal has inconsisten argument type
    checker = SyntaxChecker()
    literal1 = Literal("foo", [Number(1), Variable("y")], True)
    literal2 = Literal("foo", [String("x"), Variable("y")], True)
    with pytest.raises(TypeError):
        checker.check_literal(literal1)
        checker.check_literal(literal2)


def test_check_literal_with_inconsistent_arg_number():
    # Test that a TypeError is raised if a literal has inconsistent number of arguments
    checker = SyntaxChecker()
    literal1 = Literal("foo", [Variable("x"), Variable("y")], True)
    literal2 = Literal("foo", [Variable("x")], True)
    checker.check_literal(literal1)
    with pytest.raises(TypeError):
        checker.check_literal(literal2)


def test_check_literal_with_valid_arg_type():
    # Test that no error is raised if a literal has a valid argument type
    checker = SyntaxChecker()
    literal = Literal("foo", [Variable("x"), Variable("y")], True)
    checker.check_literal(literal)


def test_check_literal_with_consistent_arg_num():
    # Test that no error is raised if a literal has a consistent number of arguments
    checker = SyntaxChecker()
    literal1 = Literal("foo", [Variable("x"), Variable("y")], True)
    literal2 = Literal("foo", [Variable("a"), Variable("b")], True)
    checker.check_literal(literal1)
    checker.check_literal(literal2)


def test_check_rule_with_underscore_in_head():
    # Test that a TypeError is raised if a rule has an underscore in its head
    checker = SyntaxChecker()
    rule = Rule(Literal("foo", [Underscore(), Variable("y")], True), [])
    with pytest.raises(TypeError):
        checker.check_rule(rule)


def test_check_rule_with_ungrounded_variables():
    # Test that a TypeError is raised if a rule has ungrounded variables in its head
    checker = SyntaxChecker()
    rule = Rule(
        Literal("foo", [Variable("x"), Variable("z")], True),
        [Literal("bar", [Variable("x"), Variable("y")], True)],
    )
    with pytest.raises(TypeError):
        checker.check_rule(rule)


def test_check_rule_with_negated_head():
    # Test that a TypeError is raised if a rule has a negated head
    checker = SyntaxChecker()
    rule = Rule(Literal("foo", [Variable("x"), Variable("y")], False), [])
    with pytest.raises(TypeError):
        checker.check_rule(rule)


def test_check_fact_with_non_constant_args():
    # Test that a TypeError is raised if a fact has non-constant arguments
    checker = SyntaxChecker()
    fact = Rule(Literal("foo", [Variable("x"), Variable("y")], True), [])
    with pytest.raises(TypeError):
        checker.check_fact(fact)


def test_check_fact_with_constant_args():
    # Test that no error is raised if a fact has constant arguments
    checker = SyntaxChecker()
    fact = Fact("foo", [String("x"), Number(1)])
    checker.check_fact(fact)
