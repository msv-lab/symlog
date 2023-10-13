import pytest
from symlog.souffle import (
    Rule,
    Literal,
    Variable,
    String,
    Number,
    SYM,
    NUM,
)
from symlog.environment import Environment


def test_infer_declarations():
    # Test that the declarations are inferred correctly from the facts and rules
    with Environment() as env:
        facts = [
            Rule(Literal("foo", [String("x"), Number(1)], True), []),
            Rule(Literal("bar", [String("x"), Number(2)], True), []),
        ]
        rules = [
            Rule(
                Literal("baz", [Variable("x"), Variable("y")], True),
                [Literal("foo", [Variable("x"), Variable("y")], True)],
            ),
            Rule(
                Literal("qux", [Variable("x"), Variable(2)], True),
                [Literal("bar", [Variable("x"), Variable(2)], True)],
            ),
        ]
        analyser = env.type_analyser
        analyser.infer_declarations(rules, facts)
        assert analyser.declarations == {
            "foo": [SYM, NUM],
            "bar": [SYM, NUM],
            "baz": [SYM, NUM],
            "qux": [SYM, NUM],
        }


def test_infer_declarations_with_multiple_inferred_types():
    # Test that a TypeError is raised if a head argument has multiple inferred types

    with Environment() as env:
        facts = [
            Rule(Literal("foo", [String("x"), Number(1)], True), []),
            Rule(Literal("baz", [Number(2), String("x")], True), []),
        ]
        rules = [
            Rule(
                Literal("bar", [Variable("x"), Variable("y")], True),
                [
                    Literal("foo", [Variable("x"), Variable("y")], True),
                    Literal("baz", [Variable("x"), Variable("y")], True),
                ],
            )
        ]
        analyser = env.type_analyser
        with pytest.raises(TypeError):
            analyser.infer_declarations(rules, facts)


if __name__ == "__main__":
    test_infer_declarations()
    test_infer_declarations_with_multiple_inferred_types()
