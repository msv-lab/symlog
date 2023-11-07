from symlog.souffle import Rule, Literal, Variable
from symlog.souffle import parse

import pytest
from lark.exceptions import UnexpectedInput


def test_parse_relation_decl():
    program_str = ".decl my_relation(x: number, y: string)"
    ast = parse(program_str)
    assert ast.declarations == {"my_relation": ["number", "string"]}


def test_parse_rule():
    program_str = "my_relation(x, y) :- other_relation(x, z), third_relation(z, y)."
    result = parse(program_str)
    assert (
        str(result.rules[0])
        == "my_relation(x, y) :- other_relation(x, z), third_relation(z, y)."
    )


def test_parse_fact():
    program_str = 'my_relation(1, "hello").'
    result = parse(program_str)
    assert str(result.facts[0]) == 'my_relation(1, "hello").'


def test_parse_input():
    program_str = ".input my_input"
    result = parse(program_str)
    assert result.inputs == ["my_input"]


def test_parse_output():
    program_str = ".output my_output"
    result = parse(program_str)
    assert result.outputs == ["my_output"]


def test_program():
    program_str = """
        .decl edge(x: number, y: number)
        .input edge
        .output path

        path(x, y) :- edge(x, y).
        path(x, z) :- path(x, y), edge(y, z).
    """

    ast = parse(program_str)

    assert ast.declarations == {"edge": ["number", "number"]}
    assert ast.inputs == ["edge"]
    assert ast.outputs == ["path"]
    assert str(ast.rules) == str(
        [
            Rule(
                Literal("path", [Variable("x"), Variable("y")], True),
                [Literal("edge", [Variable("x"), Variable("y")], True)],
            ),
            Rule(
                Literal("path", [Variable("x"), Variable("z")], True),
                [
                    Literal("path", [Variable("x"), Variable("y")], True),
                    Literal("edge", [Variable("y"), Variable("z")], True),
                ],
            ),
        ]
    )


def test_program_with_parse_error():
    program_str = """
        .decl edge(x: number, y: number)
        .input edge
        .output path

        path(x, y) :- edge(x, y), x < y.
        path(x, z) :- path(x, y), edge(y, z).
    """

    with pytest.raises(UnexpectedInput):
        parse(program_str)


if __name__ == "__main__":
    test_program_with_parse_error()
