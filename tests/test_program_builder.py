import pytest
from symlog.program_builder import ProgramBuilder
from symlog.souffle import (
    String,
    Number,
    Variable,
    Underscore,
    Literal,
    SymbolicNumberWrapper,
    SymbolicStringWrapper,
    SYM,
    NUM,
)


def test_string():
    assert isinstance(ProgramBuilder.String("test"), String)


def test_number():
    assert isinstance(ProgramBuilder.Number(1), Number)


def test_variable():
    assert isinstance(ProgramBuilder.Variable("x"), Variable)
    assert isinstance(ProgramBuilder.Variable("_"), Underscore)


def test_symbolic_constant_with_unkown_type():
    with pytest.raises(ValueError):
        ProgramBuilder.SymbolicConstant("test", "unknown_type")


def test_symbolic_constant_with_sym_type():
    sym_constant = ProgramBuilder.SymbolicConstant("test", SYM)
    assert sym_constant.name == "test"
    assert isinstance(sym_constant, SymbolicStringWrapper)


def test_symbolic_constant_with_num_type():
    num_constant = ProgramBuilder.SymbolicConstant("test", NUM)
    assert num_constant.name == "test"
    assert isinstance(num_constant, SymbolicNumberWrapper)


def test_literal():
    literal = ProgramBuilder.Literal("test", [String("x"), Number(1)], True)
    assert literal.name == "test"
    assert literal.args == [String("x"), Number(1)]
    assert literal.positive == True


def test_fact():
    fact = ProgramBuilder.Fact("test", [String("x"), Number(1)], True)
    assert fact.head.name == "test"
    assert fact.head.args == [String("x"), Number(1)]
    assert fact.symbolic_sign == True


def test_rule():
    rule = ProgramBuilder.Rule(Literal("test", [Variable("x"), Number(1)], True), [])
    assert rule.head.name == "test"
    assert rule.head.args == [Variable("x"), Number(1)]
    assert rule.body == []
